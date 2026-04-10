"use strict";

// Formatting
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

function formatTime(seconds) {
    if (seconds < 60) return `${seconds} second${seconds !== 1 ? "s" : ""}`;
    if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        if (remainingSeconds === 0) {
            return `${minutes} minute${minutes !== 1 ? "s" : ""}`;
        }
        return `${minutes} minute${minutes !== 1 ? "s" : ""} ${remainingSeconds} second${remainingSeconds !== 1 ? "s" : ""}`;
    }
    if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (minutes === 0) {
            return `${hours} hour${hours !== 1 ? "s" : ""}`;
        }
        return `${hours} hour${hours !== 1 ? "s" : ""} ${minutes} minute${minutes !== 1 ? "s" : ""}`;
    }
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    if (hours === 0) {
        return `${days} day${days !== 1 ? "s" : ""}`;
    }
    return `${days} day${days !== 1 ? "s" : ""} ${hours} hour${hours !== 1 ? "s" : ""}`;
}

// File operations
 async function compressFile(file, format = 'gzip') {
    const compressedStream = file.stream()
        .pipeThrough(new CompressionStream(format));
    
    // Convert stream to response and then to blob
    const compressedResponse = new Response(compressedStream);
    const compressedBlob = await compressedResponse.blob();
    
    // Create new file
    const compressedFile = new File(
        [compressedBlob], 
        file.name, 
        { type: 'application/gzip' }
    );
    
    return compressedFile;
}

async function decompressFile(compressedFile, format = 'gzip') {
    const decompressedStream = compressedFile.stream()
        .pipeThrough(new DecompressionStream(format));
    
    const decompressedResponse = new Response(decompressedStream);
    const decompressedBlob = await decompressedResponse.blob();
    
    return new File([decompressedBlob], compressedFile.name, {
        type: decompressedBlob.type
    });
}

// Encryption function
function generateSalt(length = 16) {
    return crypto.getRandomValues(new Uint8Array(length));
}

async function encryptFile(file, password, salt) {
    const encoder = new TextEncoder();
    
    // Derive key from password
    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        encoder.encode(password),
        "PBKDF2",
        false,
        ["deriveKey"]
    );
    
    const key = await crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt"]
    );
    
    // Read file and encrypt
    const fileData = await file.arrayBuffer();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    
    const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        fileData
    );
    
    // Combine IV + encrypted data
    const encryptedData = new Uint8Array(iv.length + encrypted.byteLength);
    encryptedData.set(iv, 0);
    encryptedData.set(new Uint8Array(encrypted), iv.length);
    
    // Return as File object
    return new File(
        [encryptedData],
        `${file.name}`,
        { type: 'application/octet-stream' }
    );
}


// Decryption

async function decryptFile(encryptedFile, password, salt, ivLength = 12) {
    // Read the encrypted file
    const encryptedData = new Uint8Array(await encryptedFile.arrayBuffer());
    const fileName = encryptedFile.name

    // Extract IV and ciphertext
    const iv = encryptedData.slice(0, ivLength);
    const ciphertext = encryptedData.slice(ivLength);
    
    const encoder = new TextEncoder();
    
    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        encoder.encode(password),
        "PBKDF2",
        false,
        ["deriveKey"]
    );
    
    const key = await crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 100000,
            hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["decrypt"]
    );
    
    // Decrypt
    try {
        const decrypted = await crypto.subtle.decrypt(
            { name: "AES-GCM", iv: iv },
            key,
            ciphertext
        );
        
        // Return as File object
        return {
            success: true,
            file: new File([decrypted], fileName, { type: 'application/octet-stream' }),
            error: null
        };
    } catch (error) {
        return {
            success: false,
            file: null,
            error: "Decryption failed - incorrect password or corrupted data"
        };
    }
}

function isCryptPossible() {
  return window.isSecureContext;
}

// label input w/ tooltip

function generateTooltippedInput(id, labelTextContent, hoverTextContent, type) {
      const label = document.createElement("label");
      label.setAttribute("for", id);
      label.className = "text-label hoverable";
      label.textContent = labelTextContent;
      label.style.marginRight = "5px";

      const hoverText = document.createElement("div");
      hoverText.className = "tooltip";
      hoverText.textContent = hoverTextContent;

      const input = document.createElement("input");
      input.type = type;
      input.id = id;

  return {label, hoverText, input}
}

