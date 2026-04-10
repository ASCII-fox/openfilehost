"use strict";

const queryButton = document.getElementById("queryButton");
const keyInput = document.getElementById("keyInput");
const result = document.getElementById("keyInfo");
const uploadResult = document.getElementById("uploadResult");
const form = document.querySelector("form");

const linkingInfo = document.getElementById("linking");
const linkToQuerySpan = document.getElementById("linkToQuerySpan");
const linkToQuery = document.getElementById("linkToQuery");

const clientInfo = document.getElementById("clientInfo");
const cryptInfo = document.getElementById("cryptInfo");
const cryptPossible = isCryptPossible();


var fileEncrypted = 0;
var salt = 0;


const origin = window.location.origin
linkingInfo.innerHTML = 

"You can directly link to the queried file via:\n" +
"<b>" + origin + "/static/download.html?key=YourDownloadKey</b>"

var serverResponse;


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
  const link = origin + "/static/download.html?key=" + key;
  console.log(link)
  linkToQuerySpan.innerText = "The link to this query is: ";
  linkToQuery.innerHTML = '';  
  linkToQuery.appendChild(document.createTextNode(link));
  linkToQuery.href = link;  // try querying
  try {
    const response = await fetch(`/query?key=${encodeURIComponent(key.trim())}`);
    const data = await response.json();
    serverResponse = data;
    fileEncrypted = data.encrypted;
    salt = data.salt;
    console.log(fileEncrypted)

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
          
          // Format size and flags
          if (dataKey == "downloadSize" || dataKey == "processedSize") {
            valueCell.textContent = formatBytes(data[dataKey]);
          } else if (dataKey == "compressed" || dataKey == "encrypted"){
            valueCell.textContent = data[dataKey] == 1 ? "True" : "False";
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

      const breakDiv = document.createElement("div");
      const brElem = document.createElement("br");
      breakDiv.className = "break"
      

      // Create container for buttons/labels
      const buttonContainer = document.createElement("div");
      buttonContainer.className = "buttonContainer";

      buttonContainer.appendChild(document.createElement("hr"))

 
      // Create decryption label if file encrypted
      if (fileEncrypted) {
        const decryptElems = generateTooltippedInput(
          "decryptContent",
          "Decryption password: ",
          "As the file is encrypted, you will need to provide the same password that was used in order to decrypt it.",
          "text");

        if (!cryptPossible) {
          decryptElems.input.disabled = true;
          decryptElems.label.style.filter = "invert(100%)";
          decryptElems.hoverText.innerText = "Can't decrypt because this environment is insecure. Please use HTTPS or ask the administrator to enable it."
        }
      const breakDiv = document.createElement("div");
      breakDiv.className = "break";

      buttonContainer.appendChild(breakDiv);
      buttonContainer.appendChild(decryptElems.label);
      buttonContainer.appendChild(decryptElems.hoverText);
      buttonContainer.appendChild(decryptElems.input);

      buttonContainer.append(brElem);
      }


      buttonContainer.appendChild(breakDiv)

      // Download button with original filename
      const downloadButton = document.createElement("button");
      downloadButton.textContent = "DOWNLOAD File";
      downloadButton.className = "button";
      downloadButton.onclick = () => downloadFile(key, fileName);
      buttonContainer.appendChild(downloadButton);
      

      // Delete button
      const deleteButton = document.createElement("button");
      deleteButton.innerHTML = "<b>DELETE</b> File";
      deleteButton.className = "buttonDestructive";
      deleteButton.onclick = () => deleteFile(key);
      buttonContainer.appendChild(deleteButton);
      
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
  const password = document.getElementById("decryptContent").value;
  const fileUrl = `/upload/${encodeURIComponent(key.trim())}`;
  cryptInfo.innerText = ""
  
  try {
    const response = await fetch(fileUrl);
    
    if (response.ok) {
      let blob = await response.blob();
      let filename = originalFileName && originalFileName !== "N/A" ? originalFileName : key;
      let file = new File([blob], filename, { type: blob.type });


      // Check if encrypted and attempt to decrypt
      if (fileEncrypted) {

        cryptInfo.innerText = "Trying to decrypt file with given password..."

        
        const saltBytes = new Uint8Array(salt.split(",").map(Number));
        const result = await decryptFile(file, password, saltBytes);

        if (result.success != true) {
          clientInfo.innerText = "Decryption failed. The password you input is most likely incorrect.";
          cryptInfo.innerText = ""
          return;
        } else {
        cryptInfo.innerText = ""

          file = result.file;
        }
      }
      
      // Check if the file was compressed on the server
      if (serverResponse.compressed === 1) {
        try {
          clientInfo.innerText = "Decompressing file...";
          
          
          // Decompress the file
          const decompressedFile = await decompressFile(file, 'gzip');
          
          // Replace blob with decompressed version
          file = decompressedFile;
          
          
          clientInfo.innerText = "Downloading...";
        } catch (decompressError) {
          console.error('Decompression failed:', decompressError);
          clientInfo.innerText = `Decompression failed: ${decompressError.message} If this file was encrypted, it is extremely likely that this is because you input an incorrect password.`;
          return;
        }
      }
      
      // Create download link
      const url = window.URL.createObjectURL(file);
      const a = document.createElement("a");
      a.style.display = "none"; 
      a.href = url;
      a.download = filename;
      
      // Use click and cleanup without appending to body if not needed
      a.click();
      window.URL.revokeObjectURL(url);
      
      clientInfo.innerText = "Download complete!";
    } else {
      clientInfo.innerText = "Download failed: File not found on server";
    }
  } catch (error) {
    clientInfo.innerText = "Download error: " + error.message;
  }
}


async function onLoad() {
  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const queryKey = urlParams.get("key");
  
  if (queryKey) {
    keyInput.value = queryKey;
    
    await performQuery(queryKey);
  }
}

async function deleteFile(key) {
    try {
        const response = await fetch(`/delete?key=${encodeURIComponent(key)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'ok') {
          console.log("delete status ok")
          clientInfo.innerHTML = "<b>Deleted file successfully.</b>";
            return true;
        } else { 
            return false;
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        return false;
    }
}
