# Claude File Renamer 📁✨

A powerful file renaming tool that uses Claude AI to intelligently analyze file content and suggest organized naming structures. This GUI application helps maintain consistent file naming conventions across teams and projects.


## Features

- **AI-Powered Analysis**: Uses Claude 3.5 Sonnet to understand file content and suggest appropriate names
- **Content Extraction**: Reads text from Word documents, PDFs, and analyzes filenames for other file types
- **Smart Fallback**: Works even when AI analysis is unavailable
- **File Collision Prevention**: Handles naming collisions automatically
- **User-Friendly Interface**: Select files to rename with easy checkboxes
- **Detailed Logs**: See exactly what's happening during the process

## Installation

### Prerequisites

- Python 3.7 or higher
- Tkinter (usually included with Python)
- An Anthropic API key (for Claude)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/claude-file-renamer.git
   cd claude-file-renamer
   ```

2. Install required packages:
   ```bash
   pip install anthropic docx2txt PyPDF2 python-dotenv
   ```

3. Run the application:
   ```bash
   python claude_renamer_gui.py
   ```

## How to Use

1. **Enter your Claude API key**
   - Sign up at [Anthropic Console](https://console.anthropic.com) if you don't already have an account
   - Generate an API key in your Anthropic Console
   - Paste the key into the API Key field (it will be masked for security)

2. **Select a directory**
   - Click "Browse" to select the folder containing files you want to rename
   - Click "Scan Directory" to find supported files (.docx, .pdf, .xlsx, .jpg, etc.)

3. **Analyze Files**
   - Click "Analyze Files" to process the files with Claude AI
   - Each file will be analyzed to determine appropriate naming elements
   - Hover over suggested names to see Claude's reasoning

4. **Rename Files**
   - Select/deselect files using the checkboxes 
   - Click "Rename Selected Files" to apply the changes
   - Confirm when prompted

## Naming Convention

The tool follows a standard naming convention for files:

```
Subject_Description_DocumentForm_YYYYMMDD_Rev#.extension
```

Where:
- **Subject**: The main topic/department (e.g., "Finance")
- **Description**: What the document is about, in CamelCase (e.g., "QuarterlyReport")
- **DocumentForm**: A three-letter code indicating document type (e.g., "RPT" for Report)
- **Date**: Format YYYYMMDD (e.g., "20240515")
- **Revision**: Version status (e.g., "Rev0" for final, "RevA" for draft)

### Document Form Codes

Common document form codes include:
- **RPT**: Report
- **MEM**: Memo
- **FRM**: Form
- **MKT**: Marketing
- **IMG**: Image
- **DAT**: Data
- **DOC**: Document
- **PRO**: Proposal
- **GUI**: Guidelines

## Privacy & Security

- Your API key is never stored and only used for the current session
- Files are processed locally on your computer
- Only file content is sent to Claude for analysis (no metadata)
- Claude's analysis is performed through secure API calls

## Customization

You can customize the document form codes by modifying the `DOCUMENT_FORMS` dictionary at the top of the script:

```python
DOCUMENT_FORMS = {
    "RPT": "Report",
    "MEM": "Memo",
    # Add your custom codes here
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for the Claude AI model
- [Python-Docx2Txt](https://github.com/ankushshah89/python-docx2txt) for Word document text extraction
- [PyPDF2](https://github.com/py-pdf/pypdf) for PDF parsing
