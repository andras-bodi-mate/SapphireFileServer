const documentFileExtensions = {
  "txt": "Text Document",
  "log": "Log File",
  "csv": "Comma-Separated Values File",
  "tsv": "Tab-Separated Values File",
  "json": "JSON File",
  "xml": "XML File",
  "yaml": "YAML File",
  "yml": "YAML File",
  "ini": "Configuration Settings",
  "md": "Markdown Document",
  "tex": "LaTeX Document",
  "srt": "SubRip Subtitle File",
  "vtt": "WebVTT Subtitle File",
  "po": "Portable Object File",
  "conf": "Configuration File",
  "sql": "SQL Database Script",
  "doc": "Microsoft Word 97-2003 Document",
  "docx": "Microsoft Word Document",
  "odt": "OpenDocument Text Document",
  "rtf": "Rich Text Format File",
  "pdf": "PDF Document",
  "wpg": "WordPerfect Graphic",
  "pages": "Apple Pages Document",
  "pub": "Microsoft Publisher Document"
};

const musicFileExtensions = {
  "mp3": "MP3 Audio File",
  "aac": "AAC Audio File",
  "m4a": "MPEG-4 Audio File",
  "ogg": "Ogg Vorbis Audio File",
  "wma": "Windows Media Audio File",
  "opus": "Opus Audio File",
  "ra": "RealAudio File",
  "mp2": "MPEG Layer II Audio File",
  "flac": "Free Lossless Audio Codec File",
  "alac": "Apple Lossless Audio Codec File",
  "ape": "Monkey's Audio File",
  "wv": "WavPack Audio File",
  "wav": "WAVE Audio File",
  "tta": "True Audio File",
  "shn": "Shorten Compressed Audio File",
  "wab": "Windows Address Book (possible mistake?)",
  "aiff": "Audio Interchange File Format",
  "aif": "Audio Interchange File Format",
  "au": "AU Audio File",
  "pcm": "Raw PCM Audio File",
  "caf": "Core Audio File"
};

const imageFileExtensions = {
  "jpg": "JPEG Image",
  "jpeg": "JPEG Image",
  "png": "Portable Network Graphics Image",
  "gif": "GIF Image",
  "bmp": "Bitmap Image",
  "tiff": "TIFF Image",
  "tif": "TIFF Image",
  "webp": "WebP Image",
  "heif": "HEIF Image",
  "heic": "HEIC Image",
  "avif": "AVIF Image",
  "ico": "Icon File",
  "cr2": "Canon RAW Image",
  "nef": "Nikon RAW Image",
  "arw": "Sony RAW Image",
  "dng": "Digital Negative Image",
  "svg": "Scalable Vector Graphics File",
  "eps": "Encapsulated PostScript File",
  "psd": "Adobe Photoshop Document",
  "xcf": "GIMP Image File",
  "exr": "OpenEXR Image File",
  "hdr": "High Dynamic Range Image"
};

const movieFileExtensions = {
  "mp4": "MPEG-4 Video File",
  "mov": "Apple QuickTime Movie",
  "avi": "Audio Video Interleave File",
  "wmv": "Windows Media Video File",
  "mkv": "Matroska Video File",
  "flv": "Flash Video File",
  "webm": "WebM Video File",
  "mpeg": "MPEG Video File",
  "mpg": "MPEG Video File",
  "3gp": "3GPP Multimedia File",
  "mxf": "Material Exchange Format File",
  "m2ts": "MPEG-2 Transport Stream File",
  "mts": "MPEG-2 Transport Stream File"
};

const codeFileExtensions = {
  "html": "HTML File",
  "htm": "HTML File",
  "css": "Cascading Style Sheets File",
  "js": "JavaScript File",
  "mjs": "JavaScript Module File",
  "cjs": "CommonJS Module File",
  "ts": "TypeScript File",
  "tsx": "TypeScript JSX File",
  "jsx": "JavaScript JSX File",
  "py": "Python Script",
  "rb": "Ruby Script",
  "php": "PHP Script",
  "pl": "Perl Script",
  "pm": "Perl Module",
  "sh": "Shell Script",
  "bash": "Bash Script",
  "zsh": "Zsh Script",
  "ps1": "PowerShell Script",
  "bat": "Batch File",
  "c": "C Source File",
  "h": "C Header File",
  "cpp": "C++ Source File",
  "cc": "C++ Source File",
  "cxx": "C++ Source File",
  "hpp": "C++ Header File",
  "hh": "C++ Header File",
  "hxx": "C++ Header File",
  "cs": "C# Source File",
  "java": "Java Source File",
  "kt": "Kotlin Source File",
  "kts": "Kotlin Script",
  "go": "Go Source File",
  "rs": "Rust Source File",
  "swift": "Swift Source File",
  "m": "Objective-C Implementation File",
  "mm": "Objective-C++ Implementation File",
  "r": "R Script",
  "R": "R Script",
  "lua": "Lua Script",
  "scala": "Scala Source File",
  "hs": "Haskell Source File",
  "dart": "Dart Source File",
  "ex": "Elixir Source File",
  "exs": "Elixir Script",
  "erl": "Erlang Source File",
  "hrl": "Erlang Header File"
};

const archiveFileExtensions = {
  "zip": "ZIP Archive",
  "rar": "RAR Archive",
  "7z": "7-Zip Archive",
  "tar": "Tape Archive File",
  "gz": "GZIP Compressed File",
  "bz2": "Bzip2 Compressed File",
  "xz": "XZ Compressed File"
};

const cadFileExtensions = {
  "dwg": "AutoCAD Drawing Database File",
  "dxf": "Drawing Exchange Format File",
  "dwt": "AutoCAD Drawing Template",
  "dws": "AutoCAD Drawing Standards File",
  "ipt": "Inventor Part File",
  "iam": "Inventor Assembly File",
  "idw": "Inventor Drawing File",
  "ipn": "Inventor Presentation File",
  "f3d": "Fusion 360 Design File",
  "catpart": "CATIA V5 Part File",
  "catproduct": "CATIA V5 Product File",
  "cgr": "CATIA Graphical Representation File",
  "prt": "CAD Part File",
  "asm": "CAD Assembly File",
  "drw": "CAD Drawing File",
  "sldprt": "SolidWorks Part File",
  "sldasm": "SolidWorks Assembly File",
  "slddrw": "SolidWorks Drawing File",
  "gpd": "Gerber Plot Data",
  "step": "STEP 3D Model File",
  "stp": "STEP 3D Model File",
  "iges": "IGES 3D Model File",
  "igs": "IGES 3D Model File",
  "sat": "ACIS 3D Model File",
  "3dm": "Rhinoceros 3D Model File",
  "jt": "Jupiter Tessellation 3D Model File"
};

const miscellaneousFileExtensionDescriptions = {
  "xlsx": "Microsoft Excel Worksheet",
  "xls": "Microsoft Excel Worksheet",
  "pptx": "Microsoft PowerPoint Presentation",
  "ppt": "Microsoft PowerPoint Presentation",
  "accdb": "Microsoft Access Database",
  "exe": "Executable File",
  "jar": "Java Archive"
}

export const fileExtensionDescriptions = {
  ...documentFileExtensions,
  ...musicFileExtensions,
  ...imageFileExtensions,
  ...movieFileExtensions,
  ...codeFileExtensions,
  ...archiveFileExtensions,
  ...cadFileExtensions,
  ...miscellaneousFileExtensionDescriptions
}

export function getFileIcon(file) {
  if (file.size === -1) {
    return "mdi-folder";
  }

  let fileExtensionStartIndex = file.name.lastIndexOf('.');

  if (fileExtensionStartIndex !== -1) {
    let fileExtension = file.name.slice(fileExtensionStartIndex + 1);
    switch (fileExtension) {
      case "xlsx": return "mdi-file-table";
      case "xls": return "mdi-file-table";
      case "gif": return "mdi-file-gif";
      case "pdf": return "mdi-file-pdf-box";
      case "pptx": return "mdi-file-powerpoint";
      case "ppt": return "mdi-file-powerpoint";
      case "docx": return "mdi-file-word";
      case "doc": return "mdi-file-word";
      case "accdb": return "mdi-database";
      case "odt": return "mdi-file-word";
      case "xml": return "mdi-file-xml";
      case "iso": return "mdi-minidisc";
      case "csv": return "mdi-file-delimited";
      case "tsv": return "mdi-file-delimited";
      case "blend": return "mdi-blender-software";
      case "blend1": return "mdi-blender-software";
    }
    if (Object.keys(documentFileExtensions).includes(fileExtension)) {
      return "mdi-file-document";
    }
    if (Object.keys(musicFileExtensions).includes(fileExtension)) {
      return "mdi-file-music";
    }
    if (Object.keys(imageFileExtensions).includes(fileExtension)) {
      return "mdi-file-image";
    }
    if (Object.keys(movieFileExtensions).includes(fileExtension)) {
      return "mdi-movie-open";
    }
    if (Object.keys(codeFileExtensions).includes(fileExtension)) {
      return "mdi-file-code";
    }
    if (Object.keys(archiveFileExtensions).includes(fileExtension)) {
      return "mdi-folder-zip";
    }
    if (Object.keys(cadFileExtensions).includes(fileExtension)) {
      return "mdi-file-cad";
    }
  }
  return "mdi-file";
}