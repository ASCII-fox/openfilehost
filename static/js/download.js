"use strict";

// Upload functionality
const queryButton = document.getElementById("queryButton");
const keyInput = document.getElementById("keyInput");
const result = document.getElementById("keyInfo");
const uploadResult = document.getElementById("uploadResult");
const form = document.querySelector("form");


form.addEventListener("submit", async function(e) {
  e.preventDefault();
  const queriedKey = keyInput.value;
  await performQuery(queriedKey);
});

async function performQuery(key) {
  // get input
  if (!key || key.trim() === "") {
    result.innerText = "Input is either invalid or empty.";
    return false;
  }

  result.innerText = "Querying...";

  // try querying
  try {
    const response = await fetch(`/query?key=${encodeURIComponent(key.trim())}`);
    const data = await response.json();

    if (data.status == "ok") {
      result.innerText = "Making table...";

      const table = document.createElement("table");
      table.className = "fileInfoTable";
      
      const tableHeader = document.createElement("thead");
      const headerRow = document.createElement("tr");
      
      ["Property", "Value"].forEach(headerText => {
        const headerCell = document.createElement("th");
        headerCell.className = "fileInfoTableHeader";
        headerCell.textContent = headerText;
        headerRow.appendChild(headerCell);
      });
      tableHeader.appendChild(headerRow);
      table.appendChild(tableHeader);
      
      const tableBody = document.createElement("tbody");
      
      // Store file info for download
      let fileName = "";
      
      // create rows for all properties except status
      Object.keys(data).forEach(dataKey => {
        if (dataKey !== "status") {
          const row = document.createElement("tr");
          
          const labelCell = document.createElement("th");
          labelCell.className = "fileInfoTableLabel";
          const label = dataKey.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
          labelCell.textContent = label;
          row.appendChild(labelCell);
          
          const valueCell = document.createElement("td");
          valueCell.className = "fileInfoTableValue";
          
          // Store fileName for download
          if (dataKey === "fileName") {
            fileName = data[dataKey];
          }
          
          // Format size
          if (dataKey == "size") {
            valueCell.textContent = formatBytes(data[dataKey]);
          } else {
            valueCell.textContent = data[dataKey] !== undefined ? data[dataKey] : "N/A";
          }
          
          row.appendChild(valueCell);
          tableBody.appendChild(row);
        }
      });
      
      table.appendChild(tableBody);
      
      result.innerHTML = "";
      result.appendChild(table);
      
      // Create container for buttons
      const buttonContainer = document.createElement("div");
      buttonContainer.className = "buttonContainer";
      
      // Download button with original filename
      const downloadButton = document.createElement("button");
      downloadButton.textContent = "Download File";
      downloadButton.className = "button";
      downloadButton.onclick = () => downloadFile(key, fileName);
      buttonContainer.appendChild(downloadButton);
      
      result.appendChild(buttonContainer);
      
      return true;

    } else if (data.status === -1) {
      result.innerText = "Could not find the specified file on the server. \nRequested key was: " + key;
      return false;
    } else {
      result.innerText = "Query failed";
      return false;
    }
  } catch (error) {
    result.innerText = "Got error: " + error.message;
    return false;
  }
}

async function downloadFile(key, originalFileName) {
  const fileUrl = `/upload/${encodeURIComponent(key.trim())}`;
  
  try {
    const response = await fetch(fileUrl);
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      
      const filename = originalFileName && originalFileName !== "N/A" ? originalFileName : key;
      a.download = filename;
      
      // Use click and cleanup without appending to body if not needed
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      result.innerText = "Download failed: File not found on server";
    }
  } catch (error) {
    result.innerText = "Download error: " + error.message;
  }
}


// On load check if query key in header
document.addEventListener("DOMContentLoaded", async function() {
  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const queryKey = urlParams.get("query");
  
  if (queryKey) {
    keyInput.value = queryKey;
    
    await performQuery(queryKey);
  }
});
