/**
 * Molecular Biology Lab Assistant - Google Apps Script
 *
 * This script integrates with Google Docs to provide:
 * - Progress tracking for lab protocols
 * - SOP display and guidance
 * - Molecular biology calculations via API
 * - Results storage in the document
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
  // Replace with your deployed API URL
  API_BASE_URL: 'https://your-api-url.com',

  // SOP repository URL (raw GitHub content)
  SOP_BASE_URL: 'https://raw.githubusercontent.com/Bluehens302/Bark_Mlenner_AiPi/main/sops/',

  // Document metadata keys
  METADATA_KEYS: {
    CURRENT_STEP: 'current_step',
    PROTOCOL_TYPE: 'protocol_type',
    START_DATE: 'start_date',
    RESULTS_HISTORY: 'results_history'
  }
};

// ============================================================================
// MENU FUNCTIONS
// ============================================================================

/**
 * Create custom menu when document opens
 */
function onOpen() {
  DocumentApp.getUi()
    .createMenu('🧬 Lab Assistant')
    .addItem('📋 Start New Protocol', 'startNewProtocol')
    .addItem('📊 View Progress', 'viewProgress')
    .addItem('🔬 Run Calculation', 'showCalculatorMenu')
    .addItem('📖 View Current SOP', 'viewCurrentSOP')
    .addItem('⏭️ Next Step', 'moveToNextStep')
    .addSeparator()
    .addItem('🔄 Refresh View', 'refreshDocument')
    .addItem('⚙️ Settings', 'showSettings')
    .addToUi();
}

// ============================================================================
// PROTOCOL WORKFLOW
// ============================================================================

/**
 * Start a new protocol workflow
 */
function startNewProtocol() {
  const ui = DocumentApp.getUi();

  // Show protocol selection dialog
  const response = ui.alert(
    'Select Protocol Type',
    'What type of cloning are you performing?\n\n' +
    '1. PCR\n' +
    '2. Gibson Assembly\n' +
    '3. Restriction/Ligation\n' +
    '4. CRISPR gRNA Design',
    ui.ButtonSet.OK_CANCEL
  );

  if (response == ui.Button.OK) {
    const protocolChoice = ui.prompt('Enter protocol number (1-4):').getResponseText();

    const protocolMap = {
      '1': 'pcr',
      '2': 'gibson_assembly',
      '3': 'restriction_ligation',
      '4': 'crispr_grna'
    };

    const protocolType = protocolMap[protocolChoice];

    if (protocolType) {
      initializeProtocol(protocolType);
    } else {
      ui.alert('Invalid selection');
    }
  }
}

/**
 * Initialize a new protocol in the document
 */
function initializeProtocol(protocolType) {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const props = PropertiesService.getDocumentProperties();

  // Save protocol metadata
  props.setProperty(CONFIG.METADATA_KEYS.PROTOCOL_TYPE, protocolType);
  props.setProperty(CONFIG.METADATA_KEYS.CURRENT_STEP, '1');
  props.setProperty(CONFIG.METADATA_KEYS.START_DATE, new Date().toISOString());
  props.setProperty(CONFIG.METADATA_KEYS.RESULTS_HISTORY, '[]');

  // Clear document and add header
  body.clear();

  const title = body.appendParagraph('Molecular Biology Protocol Tracker');
  title.setHeading(DocumentApp.ParagraphHeading.HEADING1);

  body.appendParagraph(`Protocol: ${protocolType.replace('_', ' ').toUpperCase()}`);
  body.appendParagraph(`Started: ${new Date().toLocaleString()}`);
  body.appendParagraph('─'.repeat(80));

  // Load and display first step
  displayCurrentStep();
}

/**
 * Display current step with SOP and suggested actions
 */
function displayCurrentStep() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const props = PropertiesService.getDocumentProperties();

  const protocolType = props.getProperty(CONFIG.METADATA_KEYS.PROTOCOL_TYPE);
  const currentStep = parseInt(props.getProperty(CONFIG.METADATA_KEYS.CURRENT_STEP));

  // Add section header
  body.appendParagraph('');
  const stepHeader = body.appendParagraph(`STEP ${currentStep}`);
  stepHeader.setHeading(DocumentApp.ParagraphHeading.HEADING2);

  // Load SOP content for this step
  const sopContent = loadSOPContent(protocolType, currentStep);

  if (sopContent) {
    body.appendParagraph('📖 Protocol Instructions:');
    body.appendParagraph(sopContent);
  }

  // Add calculation section
  body.appendParagraph('');
  body.appendParagraph('🔬 Calculations for this step:');
  body.appendParagraph('[Click "Run Calculation" from menu to perform calculations]');

  // Add results section
  body.appendParagraph('');
  body.appendParagraph('📊 Results:');
  body.appendParagraph('[Results will be recorded here]');

  body.appendParagraph('─'.repeat(80));
}

/**
 * Move to the next step in the protocol
 */
function moveToNextStep() {
  const props = PropertiesService.getDocumentProperties();
  const currentStep = parseInt(props.getProperty(CONFIG.METADATA_KEYS.CURRENT_STEP));

  // Increment step
  props.setProperty(CONFIG.METADATA_KEYS.CURRENT_STEP, (currentStep + 1).toString());

  // Display next step
  displayCurrentStep();

  DocumentApp.getUi().alert('Moved to Step ' + (currentStep + 1));
}

// ============================================================================
// SOP LOADING
// ============================================================================

/**
 * Load SOP content from repository
 */
function loadSOPContent(protocolType, stepNumber) {
  try {
    const sopUrl = `${CONFIG.SOP_BASE_URL}${protocolType}.md`;
    const response = UrlFetchApp.fetch(sopUrl);
    const content = response.getContentText();

    // Parse markdown to extract step content
    // This is a simple implementation - you can enhance this
    const stepPattern = new RegExp(`## Step ${stepNumber}[\\s\\S]*?(?=## Step|$)`, 'i');
    const match = content.match(stepPattern);

    return match ? match[0] : 'SOP content not found for this step.';
  } catch (e) {
    Logger.log('Error loading SOP: ' + e.message);
    return 'Unable to load SOP. Please check the repository.';
  }
}

/**
 * View current SOP in sidebar
 */
function viewCurrentSOP() {
  const props = PropertiesService.getDocumentProperties();
  const protocolType = props.getProperty(CONFIG.METADATA_KEYS.PROTOCOL_TYPE);

  if (!protocolType) {
    DocumentApp.getUi().alert('No active protocol. Please start a new protocol first.');
    return;
  }

  const sopUrl = `${CONFIG.SOP_BASE_URL}${protocolType}.md`;

  try {
    const response = UrlFetchApp.fetch(sopUrl);
    const content = response.getContentText();

    // Create HTML for sidebar
    const html = HtmlService.createHtmlOutput(
      '<pre style="white-space: pre-wrap; font-family: monospace;">' +
      content.replace(/</g, '&lt;').replace(/>/g, '&gt;') +
      '</pre>'
    )
    .setTitle('Current SOP')
    .setWidth(400);

    DocumentApp.getUi().showSidebar(html);
  } catch (e) {
    DocumentApp.getUi().alert('Error loading SOP: ' + e.message);
  }
}

// ============================================================================
// CALCULATOR INTEGRATION
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

  // Get input
  const fwdPrimer = ui.prompt('Enter forward primer sequence:').getResponseText();
  const revPrimer = ui.prompt('Enter reverse primer sequence:').getResponseText();
  const pcrType = ui.prompt('Enter PCR type (OneTaq or Q5):').getResponseText();

  // Call API
  const payload = {
    forward_primer: fwdPrimer,
    reverse_primer: revPrimer,
    pcr_type: pcrType
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.API_BASE_URL}/pcr/annealing-temp`, options);
    const result = JSON.parse(response.getContentText());

    // Insert results into document
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

/**
 * Gibson Assembly Calculation
 */
function runGibsonCalculation() {
  const ui = DocumentApp.getUi();

  const numFragments = parseInt(ui.prompt('Number of fragments:').getResponseText());
  const totalVolume = parseFloat(ui.prompt('Total reaction volume (µL):').getResponseText());

  const fragments = [];

  for (let i = 0; i < numFragments; i++) {
    const size = parseInt(ui.prompt(`Fragment ${i+1} size (bp):`).getResponseText());
    const conc = parseFloat(ui.prompt(`Fragment ${i+1} concentration (ng/µL):`).getResponseText());
    const ratio = parseFloat(ui.prompt(`Fragment ${i+1} molar ratio (default 1.0):`).getResponseText() || '1.0');

    fragments.push({
      size_bp: size,
      concentration_ng_ul: conc,
      molar_ratio: ratio
    });
  }

  const payload = {
    fragments: fragments,
    total_volume_ul: totalVolume
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.API_BASE_URL}/gibson/calculate`, options);
    const result = JSON.parse(response.getContentText());

    // Format results
    const resultData = {};
    result.fragments.forEach(f => {
      resultData[`Fragment ${f.fragment_number}`] =
        `${f.volume_ul} µL (${f.mass_ng} ng, ${f.pmol} pmol)`;
    });
    resultData['Total Volume'] = `${result.total_volume_ul} µL`;
    resultData['Molar Ratios'] = result.molar_ratios;

    insertCalculationResult('Gibson Assembly', resultData);

    ui.alert('Calculation complete! Results added to document.');
  } catch (e) {
    ui.alert('Error calling API: ' + e.message);
  }
}

/**
 * Restriction Digest Calculation
 */
function runRestrictionDigestCalculation() {
  const ui = DocumentApp.getUi();

  const dnaMass = parseFloat(ui.prompt('DNA mass (ng):').getResponseText());
  const dnaConc = parseFloat(ui.prompt('DNA concentration (ng/µL):').getResponseText());

  const payload = {
    dna_mass_ng: dnaMass,
    dna_conc_ng_ul: dnaConc
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.API_BASE_URL}/restriction/digest`, options);
    const result = JSON.parse(response.getContentText());

    insertCalculationResult('Restriction Digest', {
      'DNA Volume': `${result.dna_volume_ul} µL`,
      'Buffer Volume': `${result.buffer_volume_ul} µL`,
      'Enzyme Volume': `${result.enzyme_volume_ul} µL`,
      'Water Volume': `${result.water_volume_ul} µL`,
      'Total Volume': `${result.total_volume_ul} µL`,
      'Warning': result.warning || 'None'
    });

    ui.alert('Calculation complete! Results added to document.');
  } catch (e) {
    ui.alert('Error calling API: ' + e.message);
  }
}

/**
 * Insert:Vector Ratio Calculation
 */
function runInsertVectorCalculation() {
  const ui = DocumentApp.getUi();

  const vectorSize = parseInt(ui.prompt('Vector size (bp):').getResponseText());
  const insertSize = parseInt(ui.prompt('Insert size (bp):').getResponseText());
  const vectorConc = parseFloat(ui.prompt('Vector concentration (ng/µL):').getResponseText());
  const insertConc = parseFloat(ui.prompt('Insert concentration (ng/µL):').getResponseText());
  const ratio = parseFloat(ui.prompt('Insert:vector ratio (default 3):').getResponseText() || '3');
  const vectorMass = parseFloat(ui.prompt('Vector mass for ligation (ng):').getResponseText());

  const payload = {
    vector_size_bp: vectorSize,
    insert_size_bp: insertSize,
    vector_conc_ng_ul: vectorConc,
    insert_conc_ng_ul: insertConc,
    ratio: ratio,
    vector_mass_ng: vectorMass
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.API_BASE_URL}/ligation/insert-vector-ratio`, options);
    const result = JSON.parse(response.getContentText());

    insertCalculationResult('Insert:Vector Ratio', {
      'Vector': `${result.vector_mass_ng} ng (${result.vector_volume_ul} µL)`,
      'Insert': `${result.insert_mass_ng} ng (${result.insert_volume_ul} µL)`,
      'Ratio': `${result.ratio}:1`
    });

    ui.alert('Calculation complete! Results added to document.');
  } catch (e) {
    ui.alert('Error calling API: ' + e.message);
  }
}

/**
 * Oligo Annealing Calculation
 */
function runOligoAnnealingCalculation() {
  const ui = DocumentApp.getUi();

  const oligo1Conc = parseFloat(ui.prompt('Oligo 1 concentration (µM):').getResponseText());
  const oligo2Conc = parseFloat(ui.prompt('Oligo 2 concentration (µM):').getResponseText());
  const desiredConc = parseFloat(ui.prompt('Desired final concentration (µM):').getResponseText());
  const finalVol = parseFloat(ui.prompt('Final volume (µL):').getResponseText());

  const payload = {
    oligo1_conc_uM: oligo1Conc,
    oligo2_conc_uM: oligo2Conc,
    desired_conc_uM: desiredConc,
    final_volume_ul: finalVol
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(`${CONFIG.API_BASE_URL}/oligo/annealing`, options);
    const result = JSON.parse(response.getContentText());

    insertCalculationResult('Oligo Annealing', {
      'Oligo 1 Volume': `${result.oligo1_volume_ul} µL`,
      'Oligo 2 Volume': `${result.oligo2_volume_ul} µL`,
      'Water Volume': `${result.water_volume_ul} µL`,
      'Final Volume': `${result.final_volume_ul} µL`,
      'Final Concentration': `${result.final_concentration_uM} µM`
    });

    ui.alert('Calculation complete! Results added to document.');
  } catch (e) {
    ui.alert('Error calling API: ' + e.message);
  }
}

// ============================================================================
// DOCUMENT MANIPULATION
// ============================================================================

/**
 * Insert calculation result into document
 */
function insertCalculationResult(calculationType, resultData) {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const cursor = doc.getCursor();

  // Find or create results section
  let insertPoint = cursor ? cursor.getElement() : body;

  // Add timestamp
  const timestamp = new Date().toLocaleString();

  // Insert results
  const resultSection = body.appendParagraph('');
  resultSection.appendText(`🔬 ${calculationType} - ${timestamp}`).setBold(true);

  const table = body.appendTable();

  for (const [key, value] of Object.entries(resultData)) {
    const row = table.appendTableRow();
    row.appendTableCell(key).setBold(true);
    row.appendTableCell(value.toString());
  }

  body.appendParagraph('');

  // Save to history
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
  const protocolType = props.getProperty(CONFIG.METADATA_KEYS.PROTOCOL_TYPE);
  const currentStep = props.getProperty(CONFIG.METADATA_KEYS.CURRENT_STEP);
  const startDate = props.getProperty(CONFIG.METADATA_KEYS.START_DATE);
  const historyJson = props.getProperty(CONFIG.METADATA_KEYS.RESULTS_HISTORY) || '[]';
  const history = JSON.parse(historyJson);

  let message = `Protocol: ${protocolType || 'None'}\n`;
  message += `Current Step: ${currentStep || 'N/A'}\n`;
  message += `Started: ${startDate ? new Date(startDate).toLocaleString() : 'N/A'}\n`;
  message += `\nCalculations Performed: ${history.length}\n`;

  if (history.length > 0) {
    message += '\nRecent calculations:\n';
    history.slice(-5).forEach(item => {
      message += `- ${item.type} (${item.timestamp})\n`;
    });
  }

  DocumentApp.getUi().alert('Progress Summary', message, DocumentApp.getUi().ButtonSet.OK);
}

/**
 * Refresh document view
 */
function refreshDocument() {
  displayCurrentStep();
  DocumentApp.getUi().alert('Document refreshed');
}

/**
 * Show settings dialog
 */
function showSettings() {
  const ui = DocumentApp.getUi();
  ui.alert(
    'Settings',
    `API URL: ${CONFIG.API_BASE_URL}\n` +
    `SOP Repository: ${CONFIG.SOP_BASE_URL}\n\n` +
    'To update these settings, edit the CONFIG object in the script.',
    ui.ButtonSet.OK
  );
}
