// --- CONFIGURATION ---
const GEMINI_API_KEY = ""; 
const CALENDAR_NAME = "Team Timer";
const PROTOCOL_DOC_ID = "1atFfk3Az7PwTx6VLN4wbzvV8enqACNCM7E1COkwZD4A"; // <--- New Variable!

function runDailyHandover() {
  const doc = DocumentApp.getActiveDocument();
  const body = doc.getBody();
  const notebookText = body.getText().slice(-2000); // Last 2000 chars of notes
  
  // 1. READ THE MASTER PROTOCOLS
  const protocolText = DocumentApp.openById(PROTOCOL_DOC_ID).getBody().getText();
  
  // 2. Check Calendar
  const nextStudent = getNextStudent();
  console.log("Planning handover for: " + nextStudent);
  
  // 3. Ask Gemini (Sending both Notes AND Protocols)
  const advice = callGemini(notebookText, protocolText, nextStudent);
  
  // 4. Append to Doc
  const timestamp = new Date().toLocaleDateString();
  const divider = `\n\n--- 🤖 AI HANDOVER (${timestamp}) ---\n`;
  const finalMessage = `${divider}TO: ${nextStudent}\n${advice}\n----------------------------------\n`;
  
  body.appendParagraph(finalMessage);
}

function getNextStudent() {
  const calendars = CalendarApp.getCalendarsByName(CALENDAR_NAME);
  if (calendars.length === 0) return "The Incoming Student";
  const cal = calendars[0];
  
  const now = new Date();
  const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  const events = cal.getEvents(now, tomorrow);
  
  for (let i = 0; i < events.length; i++) {
    const title = events[i].getTitle();
    if (title.includes("Shift:")) {
      return title.replace("Shift:", "").trim();
    }
  }
  return "The Next Student";
}

function callGemini(notes, protocols, student) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${GEMINI_API_KEY}`;
  
  const prompt = `
    You are an expert Molecular Biology Lab Manager.
    
    🛑 REFERENCE MATERIAL (STRICTLY FOLLOW THESE PROTOCOLS):
    ${protocols}
    
    CONTEXT:
    Incoming Student: ${student}
    Recent Lab Notebook Entries: "${notes}"
    
    TASK:
    1. Identify what was just done based on the notes.
    2. Determine the NEXT step based on the Reference Protocols above while also considering the current step in the General Research Pipeline.
    3. Provide technical instructions for ${student} including where to find necessary materials if listed in recent entry.
    4. If the student deviated from the protocol, gently correct them.
    5. If there is no clear next step, direct the student to talk with Austin
  `;

  const payload = {"contents": [{"parts": [{"text": prompt}]}]};
  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload)
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    return data.candidates[0].content.parts[0].text;
  } catch (e) { return "Error: " + e.toString(); }
}
// --- INTERACTIVE HELP TOOLS ---

// 1. Add the Menu when the Doc opens
function onOpen() {
  DocumentApp.getUi()
      .createMenu('🧬 Lab Manager')
      .addItem('❓ Explain Highlighted Text', 'explainHighlight')
      .addItem('📝 Draft Protocol for Highlight', 'draftProtocol')
      .addSeparator()
      .addItem('🔄 Force Daily Handover', 'runDailyHandover')
      .addToUi();
}

// 2. The function to explain what is highlighted
function explainHighlight() {
  const doc = DocumentApp.getActiveDocument();
  const selection = doc.getSelection();
  const ui = DocumentApp.getUi();

  if (!selection) {
    ui.alert("Please highlight the text you want Gemini to explain first!");
    return;
  }

  const elements = selection.getRangeElements();
  const textToExplain = elements[0].getElement().getText(); // Grabs the first highlighted chunk
  
  // Show a "Processing" toast message
  doc.setName(doc.getName()); // Tiny hack to force a UI refresh
  ui.alert("🤖 Gemini is thinking... (Click OK to continue)");

  const prompt = `
    You are a helpful Molecular Biology teaching assistant.
    The student is asking about this specific text from our lab notebook: "${textToExplain}"
    
    Please provide a clear, technical explanation of what this means and why we do it. 
    Keep it under 3 sentences.
  `;

  // Re-use your existing callGemini logic (slightly modified for raw text return)
  // We use a simplified call here to ensure it fits the comment format
  const explanation = quickGeminiCall(prompt);
  
  // Post the answer as a Comment on the text
  // Note: Apps Script can't easily "Insert Comment" via API yet, 
  // so we will append it in [brackets] right after the text nicely.
  
  const range = elements[0].getElement();
  const text = range.getText();
  
  // Insert the explanation in bold blue text
  const parent = range.getParent();
  const index = parent.getChildIndex(range);
  
  parent.insertText(index + 1, `\n\n[🤖 AI HELP: ${explanation}]\n\n`);
}

function draftProtocol() {
   // Similar to above, but asks for a step-by-step protocol
   const doc = DocumentApp.getActiveDocument();
   const selection = doc.getSelection();
   if (!selection) return;
   
   const textToExplain = selection.getRangeElements()[0].getElement().getText();
   const prompt = `Write a step-by-step numbered protocol for: ${textToExplain}`;
   
   const response = quickGeminiCall(prompt);
   
   const body = doc.getBody();
   body.appendParagraph(`\n--- 📝 PROTOCOL DRAFT: ${textToExplain} ---\n${response}\n------------------\n`);
}

// Helper function for these quick interactions
function quickGeminiCall(customPrompt) {
  // Uses the same key you defined at the top
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${GEMINI_API_KEY}`;
  const payload = {"contents": [{"parts": [{"text": customPrompt}]}]};
  const options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload)
  };
  try {
    const response = UrlFetchApp.fetch(url, options);
    const data = JSON.parse(response.getContentText());
    return data.candidates[0].content.parts[0].text;
  } catch (e) { return "Error: " + e.toString(); }
}
