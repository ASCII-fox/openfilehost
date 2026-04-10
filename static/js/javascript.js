"use strict";

console.log(window.location.origin);

// Upload functionality
const uploadButton = document.getElementById("uploadButton");
const uploadResult = document.getElementById("uploadResult");
const compressionResult = document.getElementById("compressionResult");
const serverPolicies = document.getElementById("serverPolicies");
const fileInfoDiv = document.getElementById("fileInfo");
const form = document.querySelector("form");
const origin = window.location.origin

const cryptPossible = isCryptPossible();
// Config
const fileLifetime = document.getElementById("fileLifetime");
const fileNameRemove = document.getElementById("removeFileName");
const encryptPwElement = document.getElementById("encryptionPassword")

fileInput.addEventListener("change", function() {
  const file = this.files[0];
  if (!file) {
    fileInfoDiv.textContent = "No file selected.";
    uploadButton.disabled = true;
    return;
  }

  const fileSizeFormatted = formatBytes(file.size);
  const fileLastModified = new Date(file.lastModified).toLocaleString();
  
  fileInfoDiv.textContent = 
    "File Name: " + file.name + "\n" +
    "File Size: " + fileSizeFormatted + " (" + file.size + " bytes)\n" +
    "File Last Modified: " + fileLastModified + "\n";
  
  uploadButton.disabled = false;
});

async function generateConfiguredFile(file, compressFlag, fileNameRemoveFlag) {

  // Remove file name if needed
  var fileName = file.name;

  const extension = file.name.includes('.') 
          ? '.' + file.name.split('.').pop()
          : '';
  if (fileNameRemoveFlag)
    fileName = "NONE_PROVIDED" + extension;


  // gzip compression step
  if (compressFlag[0] == true) {
      try {
          compressionResult.textContent = "Compressing file...";
          const originalSize = file.size;
          var becameLarger = false;
         
          const compressed = await compressFile(file, 'gzip');
          const compressedSize = compressed.size;
          if (compressed.size < originalSize) {
            file = compressed;
          } else {
            compressFlag[0] = false;
            becameLarger = true;
          }
           compressionResult.textContent = (compressFlag[0]) ?
              "Successfully compressed file. " + `${formatBytes(originalSize)} -> ${formatBytes(file.size)} `:
              "Tried to compress file, but it became larger. Reverting to original: " + `${formatBytes(originalSize)} -> ${formatBytes(compressedSize)}`;

          
      } catch (error) {
          compressionResult.textContent = "Compression failed: " + error.message;
          return;
      }
  }



  return new File([file], fileName, {
          type: file.type,
          lastModified: file.lastModified
      });
}

// File upload
form.addEventListener("submit", async function(e) {
  e.preventDefault();

  compressionResult.textContent = "";

  var file = fileInput.files[0];
  var fileTime = parseInt(fileLifetime.value);
  if (isNaN(fileTime))
    fileTime = -1;
  if (!file) return;

  const originalFileSize = file.size

  // Compress and rename file if needed
  var compressFlag = [document.getElementById('compressFile')?.checked];
  const fileNameRemoveFlag = fileNameRemove.checked;
  file = await generateConfiguredFile(file, compressFlag, fileNameRemoveFlag);

  // Encrypt if needed
  const needEncryptFile = (encryptPwElement.value != "");
  const salt = generateSalt();
  if (needEncryptFile) {
    file = await encryptFile(file, encryptPwElement.value, salt)
  }

  
  uploadResult.textContent = "Uploading...";
  
  const formData = new FormData();
  formData.append("file", file);
  formData.append("life", fileTime);
  formData.append("compressed", compressFlag[0]);
  formData.append("originalFileSize", originalFileSize);
  formData.append("encrypted", needEncryptFile);
  formData.append('salt', salt);
  
  
  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const result = await response.json();

    if (result.status == "ok") {
      console.log(result);
      const query = origin + "/static/download.html?key=" + result.key
      const reportedLifetimeValue = (result.life == -1) ? "Hidden by server." : result.life; 
      uploadResult.innerHTML = "Message from server: " + result.message + "\n" +
                               "Download key: " + result.key + "\n" +
                               "File lifetime: " + reportedLifetimeValue + "\n" +
                                "<hr class='break'>" +

                               "Query link: <a href='" + query + "'>"+ query +"</a>" ;
    } else {
      console.log(result);
      uploadResult.innerHTML = "Upload failed!\n" +
                               "Message from server: " + result.message;
    }
    
    // Reset
    fileInput.value = "";
    fileInfoDiv.textContent = "No file selected.";
    uploadButton.disabled = true;
  } catch (error) {
    uploadResult.textContent = "Upload failed";
  }
});

function checkCrypt() {
  if (!cryptPossible) {
    encryptPwElement.disabled = true;
    encryptLabel.style.filter = "invert(100%)";
    encryptTooltip.innerText = "window.isSecureContext is false. Access this page on HTTPS to enable encryption/decryption functionality.";
    clientInfo.innerText = "Encryption is disabled because crypto functions are unavailable. Access this page via HTTPS if possible to fix this."
  } else {
    clientInfo.innerText = "Encryption is enabled."
  }
}

async function queryPolicies() {

  console.log("Attempting to get policies...");
  try {
    const response = await fetch("policies", {method: "GET"});
    const result = await response.json();

    if (result.access == 1) {
      const serverLife = result.serverLifetime
      var inner = ""
      if (serverLife > 0) {
        inner = `<span id="serverTime">${serverLife} seconds</span>`
      } else {
        inner = "None. Requires manual shutdown."
      }

      serverPolicies.innerHTML =
        `Max file lifetime: ${result.fileLifetime} seconds (${formatTime(result.fileLifetime)})<br>` +
        `Time until automatic server shutdown: ${inner}`;

     if (serverLife > 0) {
      await startTimer();
     }


    } else {
      serverPolicies.innerText = "Hidden.";

    }
  } catch (error) {
      serverPolicies.innerText = `Failed to get server policies. Error: ${error}`
  }

  checkCrypt();
}

function startTimer() {
  const elem = document.getElementById("serverTime");
  var time = parseInt(elem.innerText);

  if (time == 0) {
    elem.innerText = "Server has shut down.";
    return;
  }

  time -= 1;

  elem.innerText = `${time} seconds (${formatTime(time)})`;

  setTimeout(startTimer, 1000);
}



