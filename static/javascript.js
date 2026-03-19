"use strict";

console.log("Hello");

// Upload functionality
const uploadButton = document.getElementById("uploadButton");
const uploadResult = document.getElementById("uploadResult");
const fileInfoDiv = document.getElementById("fileInfo");
const form = document.querySelector("form");

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
  
  uploadButton.disabled = false; // Enable upload button
});

form.addEventListener("submit", async function(e) {
  e.preventDefault();
  
  const file = fileInput.files[0];
  if (!file) return;
  
  uploadResult.textContent = "Uploading...";
  
  const formData = new FormData();
  formData.append("file", file);
  
  try {
    const response = await fetch("/upload", { method: "POST", body: formData });
    const result = await response.json();
    uploadResult.innerHTML = `Uploaded: <a href="/uploaded/${result.filename}" target="_blank">${result.filename}</a>`;
    
    // Reset
    fileInput.value = "";
    fileInfoDiv.textContent = "No file selected.";
    uploadButton.disabled = true;
  } catch (error) {
    uploadResult.textContent = "Upload failed";
  }
});
