/**
 * Molecular Biology Lab Assistant - Google Apps Script v2
 * Updated to work with SOP subsections from PDF files
 *
 * This script integrates with Google Docs to provide:
 * - Browse and select SOP sections
 * - Display only relevant subsections
 * - Link sections to appropriate calculators
 * - Progress tracking
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  // Replace with your deployed API URL
  API_BASE_URL: 'https://bark-mlenner-aipi-1.onrender.com',

  // Document metadata keys
  METADATA_KEYS: {
    CURRENT_SOP: 'current_sop',
    CURRENT_SECTION: 'current_section',
    START_DATE: 'start_date',
    RESULTS_HISTORY: 'results_history',
    SECTIONS_COMPLETED: 'sections_completed'
  },

  // Retry settings for cold starts
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 2000  // 2 seconds between retries
};

// ============================================================================
// API HELPER WITH RETRY LOGIC
// ============================================================================

/**
 * Fetch from API with retry logic for cold starts
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @returns {HTTPResponse} - The response
 */
function fetchWithRetry(url, options = {}) {
  options.muteHttpExceptions = true;

  for (let attempt = 1; attempt <= CONFIG.MAX_RETRIES; attempt++) {
    try {
      const response = UrlFetchApp.fetch(url, options);
      const responseCode = response.getResponseCode();

      // Success
      if (responseCode >= 200 && responseCode < 300) {
        return response;
      }

      // Server errors (502, 503, 504) - might be cold start
      if (responseCode >= 502 && responseCode <= 504) {
        if (attempt < CONFIG.MAX_RETRIES) {
          Logger.log(`Attempt ${attempt} failed with ${responseCode}, retrying in ${CONFIG.RETRY_DELAY_MS}ms...`);
          Utilities.sleep(CONFIG.RETRY_DELAY_MS);
          continue;
        }
      }

      // Other errors - don't retry
      throw new Error(`HTTP ${responseCode}: ${response.getContentText()}`);

    } catch (e) {
      if (attempt < CONFIG.MAX_RETRIES && (e.message.includes('502') || e.message.includes('503') || e.message.includes('504'))) {
        Logger.log(`Attempt ${attempt} failed: ${e.message}, retrying...`);
        Utilities.sleep(CONFIG.RETRY_DELAY_MS);
        continue;
      }
      throw e;
    }
  }

  throw new Error('API request failed after ' + CONFIG.MAX_RETRIES + ' attempts. Server may be starting up (cold start).');
}

// ============================================================================
// MENU FUNCTIONS
// ============================================================================

/**
 * Create custom menu when document opens
 */
function onOpen() {
  DocumentApp.getUi()
    .createMenu('🧬 Lab Assistant')
    .addItem('📋 Browse SOPs', 'browseSOPs')
    .addItem('📖 View Current Section', 'viewCurrentSection')
    .addItem('🔬 Run Calculation', 'showCalculatorMenu')
    .addItem('✅ Mark Section Complete', 'markSectionComplete')
    .addSeparator()
    .addItem('📊 View Progress', 'viewProgress')
    .addItem('🔍 Search SOPs', 'searchSOPs')
    .addItem('🔄 Refresh View', 'refreshDocument')
    .addSeparator()
    .addItem('⚡ Wake Up API', 'wakeUpAPI')
    .addToUi();
}

/**
 * Wake up the API (useful for Render free tier cold starts)
 */
function wakeUpAPI() {
  const ui = DocumentApp.getUi();

  ui.alert('Waking up API...', 'Please wait 10-20 seconds...', ui.ButtonSet.OK);

  try {
    const response = fetchWithRetry(`${CONFIG.API_BASE_URL}/`);
    const data = JSON.parse(response.getContentText());

    ui.alert('API is Ready!', `Connected to: ${data.message}\nVersion: ${data.version}`, ui.ButtonSet.OK);
  } catch (e) {
    ui.alert('Wake Up Failed', `Could not connect to API: ${e.message}`, ui.ButtonSet.OK);
  }
}

// ============================================================================
// SOP BROWSING
// ============================================================================

/**
 * Browse available SOPs
 */
function browseSOPs() {
  const ui = DocumentApp.getUi();

  try {
    // Fetch list of SOPs from API
    const response = fetchWithRetry(`${CONFIG.API_BASE_URL}/sops/list`);
    const data = JSON.parse(response.getContentText());

    if (data.count === 0) {
      ui.alert('No SOPs found', 'No SOP files are available in the repository.', ui.ButtonSet.OK);
      return;
    }

    // Build selection dialog
    let message = 'Available SOPs:\n\n';
    data.sops.forEach((sop, index) => {
      message += `${index + 1}. ${sop.filename}\n`;
    });
    message += '\nEnter the number of the SOP you want to view:';

    const response2 = ui.prompt('Select SOP', message, ui.ButtonSet.OK_CANCEL);

    if (response2.getSelectedButton() == ui.Button.OK) {
      const selection = parseInt(response2.getResponseText()) - 1;

      if (selection >= 0 && selection < data.sops.length) {
        const selectedSOP = data.sops[selection];
        browseSections(selectedSOP.sop_id, selectedSOP.filename);
      } else {
        ui.alert('Invalid selection');
      }
    }
  } catch (e) {
    ui.alert('Error', `Failed to load SOPs: ${e.message}`, ui.ButtonSet.OK);
    Logger.log('Error browsing SOPs: ' + e);
  }
}

/**
 * Browse sections within an SOP
 */
function browseSections(sopId, sopFilename) {
  const ui = DocumentApp.getUi();

  try {
    // Fetch sections from API
    const url = `${CONFIG.API_BASE_URL}/sops/${encodeURIComponent(sopId)}/sections`;
    const response = fetchWithRetry(url);
    const data = JSON.parse(response.getContentText());

    if (data.count === 0) {
      ui.alert(
        'No Sections Found',
        'This SOP does not have numbered sections that can be parsed.\n\n' +
        'SOP protocol not found.',
        ui.ButtonSet.OK
      );
      return;
    }

    // Build selection dialog
    let message = `Sections in ${sopFilename}:\n\n`;
    data.sections.forEach((section, index) => {
      message += `${index + 1}. ${section.full_heading}\n`;
    });
    message += '\nEnter the number of the section you want to view:';

    const response2 = ui.prompt('Select Section', message, ui.ButtonSet.OK_CANCEL);

    if (response2.getSelectedButton() == ui.Button.OK) {
      const selection = parseInt(response2.getResponseText()) - 1;

      if (selection >= 0 && selection < data.sections.length) {
        const selectedSection = data.sections[selection];
        loadAndDisplaySection(sopId, selectedSection.section_number, sopFilename);
      } else {
        ui.alert('Invalid selection');
      }
    }
  } catch (e) {
    if (e.message.includes('404')) {
      ui.alert('SOP Not Found', 'SOP protocol not found.', ui.ButtonSet.OK);
    } else {
      ui.alert('Error', `Failed to load sections: ${e.message}`, ui.ButtonSet.OK);
    }
    Logger.log('Error browsing sections: ' + e);
  }
}

/**
 * Load and display a specific section
 */
function loadAndDisplaySection(sopId, sectionNumber, sopFilename) {
  const ui = DocumentApp.getUi();

  try {
    // Fetch full section content from API
    const url = `${CONFIG.API_BASE_URL}/sops/${encodeURIComponent(sopId)}/sections/${encodeURIComponent(sectionNumber)}`;
    const response = fetchWithRetry(url);
    const section = JSON.parse(response.getContentText());

    // Save current section to document properties
    const props = PropertiesService.getDocumentProperties();
    props.setProperty(CONFIG.METADATA_KEYS.CURRENT_SOP, sopId);
    props.setProperty(CONFIG.METADATA_KEYS.CURRENT_SECTION, sectionNumber);

    if (!props.getProperty(CONFIG.METADATA_KEYS.START_DATE)) {
      props.setProperty(CONFIG.METADATA_KEYS.START_DATE, new Date().toISOString());
    }

    // Display section in document
    displaySection(section, sopFilename);

    ui.alert('Section Loaded', 'Section has been loaded into the document.', ui.ButtonSet.OK);
  } catch (e) {
    if (e.message.includes('404')) {
      ui.alert('Section Not Found', 'SOP protocol not found.', ui.ButtonSet.OK);
    } else {
      ui.alert('Error', `Failed to load section: ${e.message}`, ui.ButtonSet.OK);
    }
    Logger.log('Error loading section: ' + e);
  }
}

/**
 * Display section content in the document
 */
function displaySection(section, sopFilename) {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();

  // Add section header
  body.appendParagraph('');
  const header = body.appendParagraph(`📖 ${sopFilename}`);
  header.setHeading(DocumentApp.ParagraphHeading.HEADING1);

  const sectionTitle = body.appendParagraph(section.full_heading);
  sectionTitle.setHeading(DocumentApp.ParagraphHeading.HEADING2);

  // Add section content
  body.appendParagraph('');
  const contentPara = body.appendParagraph(section.content);
  contentPara.setSpacingBefore(10);
  contentPara.setSpacingAfter(10);

  // Add suggested calculators if any
  if (section.suggested_calculators && section.suggested_calculators.length > 0) {
    body.appendParagraph('');
    const calcHeader = body.appendParagraph('🔬 Suggested Calculators for this Section:');
    calcHeader.setBold(true);

    const calcList = section.suggested_calculators.map(calc => {
      const calcNames = {
        'pcr': 'PCR Annealing Temperature',
        'gibson': 'Gibson Assembly',
        'restriction': 'Restriction Digest',
        'ligation': 'Insert:Vector Ratio',
        'oligo': 'Oligo Annealing'
      };
      return `• ${calcNames[calc] || calc}`;
    }).join('\n');

    body.appendParagraph(calcList);
    body.appendParagraph('Use "Run Calculation" from the menu to perform these calculations.');
  }

  // Add results section
  body.appendParagraph('');
  body.appendParagraph('─'.repeat(80));
  const resultsHeader = body.appendParagraph('📊 Results:');
  resultsHeader.setBold(true);
  body.appendParagraph('[Results will be recorded here when you run calculations]');
  body.appendParagraph('');
  body.appendParagraph('─'.repeat(80));

  // Add timestamp
  body.appendParagraph(`Section loaded: ${new Date().toLocaleString()}`);
}

// ============================================================================
// SEARCH FUNCTION
// ============================================================================

/**
 * Search for sections across all SOPs
 */
function searchSOPs() {
  const ui = DocumentApp.getUi();

  const response = ui.prompt(
    'Search SOPs',
    'Enter search term (searches section titles and content):',
    ui.ButtonSet.OK_CANCEL
  );

  if (response.getSelectedButton() != ui.Button.OK) {
    return;
  }

  const query = response.getResponseText().trim();
  if (!query) {
    ui.alert('Please enter a search term');
    return;
  }

  try {
    const url = `${CONFIG.API_BASE_URL}/sops/search?q=${encodeURIComponent(query)}`;
    const apiResponse = fetchWithRetry(url);
    const data = JSON.parse(apiResponse.getContentText());

    if (data.count === 0) {
      ui.alert('No Results', 'SOP protocol not found.', ui.ButtonSet.OK);
      return;
    }

    // Build results dialog
    let message = `Found ${data.count} matching section(s):\n\n`;
    data.results.slice(0, 10).forEach((result, index) => {
      message += `${index + 1}. [${result.sop_filename}] ${result.full_heading}\n`;
      message += `   Preview: ${result.content_preview.substring(0, 60)}...\n\n`;
    });

    if (data.count > 10) {
      message += `\n(Showing first 10 of ${data.count} results)\n`;
    }

    message += '\nEnter the number to view that section:';

    const response2 = ui.prompt('Search Results', message, ui.ButtonSet.OK_CANCEL);

    if (response2.getSelectedButton() == ui.Button.OK) {
      const selection = parseInt(response2.getResponseText()) - 1;

      if (selection >= 0 && selection < Math.min(10, data.count)) {
        const selected = data.results[selection];
        loadAndDisplaySection(selected.sop_id, selected.section_number, selected.sop_filename);
      } else {
        ui.alert('Invalid selection');
      }
    }
  } catch (e) {
    ui.alert('Error', `Search failed: ${e.message}`, ui.ButtonSet.OK);
    Logger.log('Search error: ' + e);
  }
}

// ============================================================================
// VIEW FUNCTIONS
// ============================================================================

/**
 * View current section again
 */
function viewCurrentSection() {
  const props = PropertiesService.getDocumentProperties();
  const sopId = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SOP);
  const sectionNumber = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SECTION);

  if (!sopId || !sectionNumber) {
    DocumentApp.getUi().alert(
      'No Active Section',
      'No section is currently loaded. Use "Browse SOPs" to select a section.',
      DocumentApp.getUi().ButtonSet.OK
    );
    return;
  }

  try {
    const url = `${CONFIG.API_BASE_URL}/sops/${encodeURIComponent(sopId)}/sections/${encodeURIComponent(sectionNumber)}`;
    const response = fetchWithRetry(url);
    const section = JSON.parse(response.getContentText());

    displaySection(section, sopId);
  } catch (e) {
    DocumentApp.getUi().alert('Error', `Failed to reload section: ${e.message}`, DocumentApp.getUi().ButtonSet.OK);
  }
}

/**
 * Mark current section as complete
 */
function markSectionComplete() {
  const props = PropertiesService.getDocumentProperties();
  const sopId = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SOP);
  const sectionNumber = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SECTION);

  if (!sopId || !sectionNumber) {
    DocumentApp.getUi().alert('No active section to mark complete');
    return;
  }

  // Track completed sections
  const completedJson = props.getProperty(CONFIG.METADATA_KEYS.SECTIONS_COMPLETED) || '[]';
  const completed = JSON.parse(completedJson);

  completed.push({
    sop_id: sopId,
    section_number: sectionNumber,
    completed_at: new Date().toISOString()
  });

  props.setProperty(CONFIG.METADATA_KEYS.SECTIONS_COMPLETED, JSON.stringify(completed));

  // Add completion marker to document
  const body = DocumentApp.getActiveDocument().getBody();
  body.appendParagraph('');
  const marker = body.appendParagraph(`✅ Section ${sectionNumber} marked complete - ${new Date().toLocaleString()}`);
  marker.setBold(true);
  body.appendParagraph('─'.repeat(80));

  DocumentApp.getUi().alert('Section marked as complete!\n\nUse "Browse SOPs" to select the next section.');
}

// ============================================================================
// CALCULATOR INTEGRATION (Same as before)
// ============================================================================

/**
 * Show calculator menu
 */
function showCalculatorMenu() {
  const ui = DocumentApp.getUi();

  const response = ui.alert(
    'Select Calculation Type',
    'Choose a calculation:\n\n' +
    '1. PCR Annealing Temperature\n' +
    '2. Gibson Assembly\n' +
    '3. Restriction Digest\n' +
    '4. Insert:Vector Ratio\n' +
    '5. Oligo Annealing',
    ui.ButtonSet.OK_CANCEL
  );

  if (response == ui.Button.OK) {
    const choice = ui.prompt('Enter calculation number (1-5):').getResponseText();

    switch(choice) {
      case '1':
        runPCRCalculation();
        break;
      case '2':
        runGibsonCalculation();
        break;
      case '3':
        runRestrictionDigestCalculation();
        break;
      case '4':
        runInsertVectorCalculation();
        break;
      case '5':
        runOligoAnnealingCalculation();
        break;
      default:
        ui.alert('Invalid selection');
    }
  }
}

/**
 * PCR Annealing Temperature Calculation
 */
function runPCRCalculation() {
  const ui = DocumentApp.getUi();

  const fwdPrimer = ui.prompt('Enter forward primer sequence:').getResponseText();
  const revPrimer = ui.prompt('Enter reverse primer sequence:').getResponseText();
  const pcrType = ui.prompt('Enter PCR type (OneTaq or Q5):').getResponseText();

  const payload = {
    forward_primer: fwdPrimer,
    reverse_primer: revPrimer,
    pcr_type: pcrType
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = fetchWithRetry(`${CONFIG.API_BASE_URL}/pcr/annealing-temp`, options);
    const result = JSON.parse(response.getContentText());

    insertCalculationResult('PCR Annealing Temperature', {
      'Annealing Temperature': `${result.annealing_temp}°C`,
      'Tm Forward': `${result.tm1}°C`,
      'Tm Reverse': `${result.tm2}°C`,
      'Warning': result.warning || 'None'
    });

    ui.alert('Calculation complete! Results added to document.');
  } catch (e) {
    ui.alert('Error calling API: ' + e.message);
    Logger.log('API Error: ' + e);
  }
}

// ... (Keep other calculator functions as they were)

/**
 * Insert calculation result into document
 */
function insertCalculationResult(calculationType, resultData) {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();

  const timestamp = new Date().toLocaleString();

  body.appendParagraph('');
  const resultSection = body.appendParagraph(`🔬 ${calculationType} - ${timestamp}`);
  resultSection.setBold(true);

  const table = body.appendTable();
  for (const [key, value] of Object.entries(resultData)) {
    const row = table.appendTableRow();
    row.appendTableCell(key).setBold(true);
    row.appendTableCell(value.toString());
  }

  body.appendParagraph('');

  saveResultToHistory(calculationType, resultData, timestamp);
}

/**
 * Save result to document properties
 */
function saveResultToHistory(calculationType, resultData, timestamp) {
  const props = PropertiesService.getDocumentProperties();
  const historyJson = props.getProperty(CONFIG.METADATA_KEYS.RESULTS_HISTORY) || '[]';
  const history = JSON.parse(historyJson);

  history.push({
    type: calculationType,
    data: resultData,
    timestamp: timestamp
  });

  props.setProperty(CONFIG.METADATA_KEYS.RESULTS_HISTORY, JSON.stringify(history));
}

// ============================================================================
// PROGRESS TRACKING
// ============================================================================

/**
 * View progress summary
 */
function viewProgress() {
  const props = PropertiesService.getDocumentProperties();
  const sopId = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SOP);
  const sectionNumber = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_SECTION);
  const startDate = props.getProperty(CONFIG.METADATA_KEYS.START_DATE);
  const completedJson = props.getProperty(CONFIG.METADATA_KEYS.SECTIONS_COMPLETED) || '[]';
  const completed = JSON.parse(completedJson);
  const historyJson = props.getProperty(CONFIG.METADATA_KEYS.RESULTS_HISTORY) || '[]';
  const history = JSON.parse(historyJson);

  let message = `Current SOP: ${sopId || 'None'}\n`;
  message += `Current Section: ${sectionNumber || 'N/A'}\n`;
  message += `Started: ${startDate ? new Date(startDate).toLocaleString() : 'N/A'}\n\n`;
  message += `Sections Completed: ${completed.length}\n`;
  message += `Calculations Performed: ${history.length}\n`;

  if (completed.length > 0) {
    message += '\nRecent completions:\n';
    completed.slice(-5).forEach(item => {
      message += `- Section ${item.section_number} (${new Date(item.completed_at).toLocaleString()})\n`;
    });
  }

  DocumentApp.getUi().alert('Progress Summary', message, DocumentApp.getUi().ButtonSet.OK);
}

/**
 * Refresh document view
 */
function refreshDocument() {
  viewCurrentSection();
  DocumentApp.getUi().alert('Document refreshed');
}
