/**
 * OPTIONAL permanent log of every visit / interaction / submission
 * into a Google Sheet (free). See CLAT_WISHES_SETUP.md, Step 3.
 */
function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Time", "Event", "Details", "Device", "Visit ID"]);
  }
  var d = JSON.parse(e.postData.contents);
  sheet.appendRow([new Date(d.time), d.event, d.details, d.device, d.visit]);
  return ContentService.createTextOutput("ok");
}
