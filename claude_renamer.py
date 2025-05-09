import os
import json
import argparse
import datetime
import mimetypes
import re
import time
from pathlib import Path
import anthropic
import docx2txt
import PyPDF2

# Constants for naming convention - these can be customized
DOCUMENT_FORMS = {
    "ACT": "Action Request",
    "AGD": "Agenda",
    "AGR": "Agreement",
    "ANN": "Announcement",
    "APP": "Application/Appendix",
    "ART": "Article",
    "BIO": "Biography",
    "BRC": "Brochure",
    "BRN": "Briefing Note",
    "CHT": "Chart",
    "COD": "Code",
    "COF": "Configuration File",
    "CON": "Contract",
    "COV": "Cover Page",
    "DFT": "Discussion Draft",
    "DRT": "Directory",
    "DWG": "Drawing",
    "ETD": "Electronic Thesis",
    "EXA": "Example",
    "FCT": "Fact Sheet",
    "FRM": "Form",
    "GRA": "Grant",
    "GUI": "Guidelines",
    "IMG": "Image",
    "INT": "Interview",
    "INV": "Invoice",
    "INX": "Index",
    "LCT": "Lecture",
    "LGL": "Legal Document",
    "LOG": "Log File",
    "LTR": "Letter",
    "MEM": "Memo",
    "MIN": "Minutes",
    "MKT": "Marketing",
    "MNL": "Manual",
    "MTG": "Meeting notes",
    "NSL": "Newsletter",
    "PLN": "Plan",
    "PMT": "Permit",
    "POL": "Policy",
    "PPR": "Paper",
    "PRC": "Procedure/Process",
    "PRF": "Profile",
    "PRO": "Proposal",
    "PRS": "Presentation",
    "PRL": "Press Release",
    "PST": "Poster",
    "RPT": "Report",
    "RVW": "Review",
    "SCH": "Schedule",
    "SPE": "Speech",
    "SRY": "Survey",
    "SUM": "Summary",
    "SUP": "Supplement",
    "TML": "Timeline",
    "TOR": "Terms of Reference",
    "YRB": "Year Book",
    "DAT": "Data",
    "COB": "Code Book"
}

def get_file_content(file_path):
    """Extract text content from files based on their type."""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Word documents
        if file_extension in ['.docx', '.doc']:
            try:
                return docx2txt.process(file_path)[:4000]  # First 4000 chars
            except:
                return f"Word document: {os.path.basename(file_path)}"
        
        # PDF files
        elif file_extension == '.pdf':
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    # Get first 2 pages or all pages if fewer
                    for page_num in range(min(2, len(pdf_reader.pages))):
                        text += pdf_reader.pages[page_num].extract_text() + "\n"
                    return text[:4000]  # First 4000 chars
            except:
                return f"PDF document: {os.path.basename(file_path)}"
        
        # Excel/CSV files - just return filename for analysis
        elif file_extension in ['.xlsx', '.xls', '.csv']:
            return f"Spreadsheet: {os.path.basename(file_path)}"
            
        # Images - just return filename for analysis
        elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            return f"Image: {os.path.basename(file_path)}"
            
        # Other files - just return filename
        else:
            return f"File: {os.path.basename(file_path)}"
            
    except Exception as e:
        return f"Error reading file {os.path.basename(file_path)}: {str(e)}"

def extract_date_from_filename(filename):
    """Extract date from filename if present."""
    # Look for common date patterns
    # Format: Month DD, YYYY
    month_names = ["January", "February", "March", "April", "May", "June", "July", 
                  "August", "September", "October", "November", "December"]
    
    # Try to find dates like "August 28, 2024" or "August+28,+2024"
    for month in month_names:
        pattern = fr'{month}\s*[\+_]?\s*(\d{{1,2}})[,\s\+_]+(\d{{4}})'
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            day = match.group(1)
            year = match.group(2)
            month_num = month_names.index(month) + 1
            return f"{year}{month_num:02d}{int(day):02d}"
    
    # Look for YYYY-MM-DD or YYYY/MM/DD
    date_pattern = r'(\d{4})[-/\s](\d{1,2})[-/\s](\d{1,2})'
    match = re.search(date_pattern, filename)
    if match:
        year, month, day = match.groups()
        return f"{year}{int(month):02d}{int(day):02d}"
    
    # Default to current date if no date found
    today = datetime.datetime.now()
    return today.strftime("%Y%m%d")

def extract_keywords_from_filename(filename):
    """Extract meaningful keywords from filename."""
    # Remove file extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Replace common separators with spaces
    name_clean = re.sub(r'[_\+\-\.]', ' ', name_without_ext)
    
    # Split into words
    words = name_clean.split()
    
    # Filter out common stop words and numbers
    stop_words = ['the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by']
    keywords = [word for word in words if word.lower() not in stop_words and not word.isdigit()]
    
    return keywords

def smart_fallback_naming(file_info):
    """Create intelligent fallback naming based on filename analysis."""
    src_path = file_info["src_path"]
    filename = os.path.basename(src_path)
    extension = os.path.splitext(filename)[1].lower()
    
    # Extract useful information from filename
    keywords = extract_keywords_from_filename(filename)
    date_str = extract_date_from_filename(filename)
    
    # Determine subject, description, and doc type based on keywords and extension
    if len(keywords) >= 2:
        subject = keywords[0]
        description = ''.join(word.capitalize() for word in keywords[1:min(4, len(keywords))])
    else:
        subject = keywords[0] if keywords else "Misc"
        description = "Document"
    
    # Select document form based on content/extension
    if extension in ['.xlsx', '.xls', '.csv']:
        if any('application' in kw.lower() for kw in keywords):
            doc_type = "APP"  # Application
        elif any('data' in kw.lower() for kw in keywords):
            doc_type = "DAT"  # Data
        else:
            doc_type = "DAT"  # Default for spreadsheets
    elif extension in ['.docx', '.doc']:
        if any(kw.lower() in ['report', 'reporting'] for kw in keywords):
            doc_type = "RPT"  # Report
        elif any(kw.lower() in ['memo', 'memorandum'] for kw in keywords):
            doc_type = "MEM"  # Memo
        elif any(kw.lower() in ['form'] for kw in keywords):
            doc_type = "FRM"  # Form
        else:
            doc_type = "DOC"  # Default for Word docs
    elif extension in ['.pdf']:
        if any(kw.lower() in ['report'] for kw in keywords):
            doc_type = "RPT"  # Report
        else:
            doc_type = "DOC"  # Default for PDFs
    elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
        doc_type = "IMG"  # Image
    else:
        doc_type = "MIS"  # Miscellaneous
    
    # Create filename following the convention
    new_name = f"{subject}_{description}_{doc_type}_{date_str}_Rev0{extension}"
    
    return {
        "src_path": src_path,
        "new_name": new_name,
        "reason": f"Smart fallback: Used {subject} as subject, {description} as description, {doc_type} as document type, and extracted date {date_str}."
    }

def get_directory_summaries(directory_path):
    """Get summaries of all files in a directory."""
    summaries = []
    
    # Supported file extensions
    supported_extensions = [
        '.docx', '.doc',                     # Word documents
        '.xlsx', '.xls', '.csv',             # Excel/CSV files
        '.pdf',                              # PDF files
        '.jpg', '.jpeg', '.png', '.gif'      # Image files
    ]
    
    # Get a list of all files in the directory (no subdirectories)
    all_files = []
    for item in os.listdir(directory_path):
        file_path = os.path.join(directory_path, item)
        if os.path.isfile(file_path):
            all_files.append((file_path, item))
    
    print(f"Total files found in directory: {len(all_files)}")
    
    # Files to skip
    skip_files = ['claude_renamer.py', 'claude_renamer_gui.py', '.env']
    
    # Process each file
    for file_path, relative_path in all_files:
        # Get file extension
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        
        # Skip files that don't match our supported extensions
        if extension not in supported_extensions:
            print(f"Skipping unsupported file type: {relative_path}")
            continue
            
        # Skip certain files
        if relative_path in skip_files or relative_path.startswith('.'):
            print(f"Skipping file: {relative_path}")
            continue
            
        print(f"Processing file: {relative_path}")
        
        # Get basic file info
        try:
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            file_content = get_file_content(file_path)
            
            summaries.append({
                "path": relative_path,
                "src_path": relative_path,
                "filename": os.path.basename(file_path),
                "extension": extension,
                "size": file_size,
                "modified": datetime.datetime.fromtimestamp(file_mtime).isoformat(),
                "content": file_content[:4000] if isinstance(file_content, str) else "",
            })
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    return summaries

def create_claude_naming_suggestion(file_info, api_key, doc_forms):
    """Use Claude to generate naming suggestion for a file."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Create a tailored prompt for Claude
        prompt = f"""I need help following a standardized file naming convention for a file.

Key elements in a filename include:
- Subject or Activity (required)
- Description of what the document is (required)
- Document Form (optional): Use form codes like MEM (Memo), RPT (Report), MKT (Marketing), etc.
- Date in YYYYMMDD format (required)
- Revision (required): Use 'Rev0' for first final version, letters A,B,C for drafts

The filename format should be: Subject_Description_DocumentForm_YYYYMMDD_Rev#.extension

For example: Project_RiskManagement_GUI_20150414_Rev0.pdf

Available Document Form codes include:
ACT (Action Request), AGD (Agenda), AGR (Agreement), ANN (Announcement), APP (Application/Appendix), ART (Article), BIO (Biography), BRC (Brochure), BRN (Briefing Note), CHT (Chart), COD (Code), COF (Configuration File), CON (Contract), COV (Cover Page), DFT (Discussion Draft), DRT (Directory), DWG (Drawing), ETD (Electronic Thesis), EXA (Example), FCT (Fact Sheet), FRM (Form), GRA (Grant), GUI (Guidelines), IMG (Image), INT (Interview), INV (Invoice), INX (Index), LCT (Lecture), LGL (Legal Document), LOG (Log File), LTR (Letter), MEM (Memo), MIN (Minutes), MKT (Marketing), MNL (Manual), MTG (Meeting notes), NSL (Newsletter), PLN (Plan), PMT (Permit), POL (Policy), PPR (Paper), PRC (Procedure/Process), PRF (Profile), PRO (Proposal), PRS (Presentation), PRL (Press Release), PST (Poster), RPT (Report), RVW (Review), SCH (Schedule), SPE (Speech), SRY (Survey), SUM (Summary), SUP (Supplement), TML (Timeline), TOR (Terms of Reference), YRB (Year Book), DAT (Data), COB (Code Book)

Here is information about the file:
Filename: {file_info['filename']}
File Type: {file_info['extension']}
Content Preview: {file_info['content'][:2000] if len(file_info['content']) > 0 else "No content available"}

Please analyze this file and provide ONLY a JSON response with the following format:
```json
{{
  "subject": "Brief subject/category",
  "description": "CamelCaseDescriptionOfDocument",
  "document_form": "XXX",
  "date": "YYYYMMDD",
  "revision": "Rev0",
  "reasoning": "Brief explanation of why you chose these elements"
}}
```

The date should be extracted from the file content or filename if available, otherwise use today's date.
Choose the most appropriate document form code from the list based on content.
Keep the subject and description concise but descriptive.
"""

        # Call Claude API with the prompt
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.0,
            system="You are a file organization assistant that analyzes files and suggests appropriate names following specific naming conventions.",
            messages=[
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )

        # Parse Claude's response
        response_text = message.content[0].text
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if not json_match:
            # Try without the code block markers
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            
        if json_match:
            json_text = json_match.group(1)
            suggestion = json.loads(json_text)
            
            # Create filename following the convention
            new_name = f"{suggestion['subject']}_{suggestion['description']}_{suggestion['document_form']}_{suggestion['date']}_{suggestion['revision']}{file_info['extension']}"
            
            return {
                "src_path": file_info["src_path"],
                "new_name": new_name,
                "reason": suggestion['reasoning']
            }
        else:
            print(f"Could not parse JSON from Claude's response for {file_info['filename']}")
            print(f"Claude's response: {response_text[:200]}...")
            return smart_fallback_naming(file_info)
            
    except Exception as e:
        print(f"Error with Claude API for {file_info['filename']}: {str(e)}")
        return smart_fallback_naming(file_info)

def create_file_tree(summaries, api_key):
    """Process each file with Claude and get back organized structure."""
    # If no files, return empty list
    if not summaries:
        print("No files to organize.")
        return []

    # Use Claude to generate naming suggestions
    files = []
    doc_forms_str = ', '.join([f"{k} ({v})" for k, v in DOCUMENT_FORMS.items()])
    
    # Process each file
    for i, file_info in enumerate(summaries):
        print(f"Analyzing file {i+1}/{len(summaries)}: {file_info['filename']}")
        
        try:
            # Use Claude to generate naming suggestion
            suggestion = create_claude_naming_suggestion(file_info, api_key, doc_forms_str)
            
            # Check if this name would cause a collision and add a unique identifier if needed
            file_dir = os.path.dirname(os.path.join(os.getcwd(), file_info["src_path"]))
            new_name_base = os.path.splitext(suggestion["new_name"])[0]
            extension = os.path.splitext(suggestion["new_name"])[1]
            
            # Check for file name collisions
            unique_id = ""
            count = 0
            while os.path.exists(os.path.join(file_dir, f"{new_name_base}{unique_id}{extension}")):
                if os.path.join(file_dir, f"{new_name_base}{unique_id}{extension}") == os.path.join(file_dir, file_info["src_path"]):
                    break  # Don't need to add uniqueness if it's the same file
                count += 1
                unique_id = f"_{count}"
            
            # Update the new name with unique identifier if needed
            if unique_id:
                suggestion["new_name"] = f"{new_name_base}{unique_id}{extension}"
                suggestion["reason"] += f" (Unique identifier {unique_id} added to prevent naming collision)"
            
            files.append(suggestion)
            
            # Rate limit to avoid hitting API limits
            if i < len(summaries) - 1:
                time.sleep(0.5)  # 0.5 second delay between requests
                
        except Exception as e:
            print(f"Error processing {file_info['filename']}: {str(e)}")
            # Fall back to smart naming
            files.append(smart_fallback_naming(file_info))
    
    return files

def rename_files(src_dir, files, auto_yes=False):
    """Rename files in place following the naming convention."""
    print("\nProposed file renaming:")
    print("======================")
    
    for file in files:
        src_path = os.path.join(src_dir, file["src_path"])
        dir_name = os.path.dirname(src_path)
        new_path = os.path.join(dir_name, file["new_name"])
        
        print(f"\nFrom: {os.path.basename(src_path)}")
        print(f"To:   {file['new_name']}")
        if "reason" in file:
            print(f"Reason: {file['reason']}")
    
    if not auto_yes:
        proceed = input("\nProceed with renaming these files? (y/n): ").lower().strip()
        if proceed != 'y':
            print("Operation cancelled.")
            return
    
    # Rename files in place
    success_count = 0
    error_count = 0
    
    for file in files:
        src_path = os.path.join(src_dir, file["src_path"])
        dir_name = os.path.dirname(src_path)
        new_path = os.path.join(dir_name, file["new_name"])
        
        try:
            os.rename(src_path, new_path)
            print(f"Renamed: {os.path.basename(src_path)} -> {file['new_name']}")
            success_count += 1
        except Exception as e:
            print(f"Error renaming {src_path}: {str(e)}")
            error_count += 1
    
    print(f"\nRenamed {success_count} files successfully. {error_count} files failed.")

def main():
    parser = argparse.ArgumentParser(description="Claude-Powered File Renamer - Rename files using standardized naming conventions")
    parser.add_argument("directory", help="Directory containing files to rename")
    parser.add_argument("--auto-yes", action="store_true", help="Automatically proceed without confirmation")
    parser.add_argument("--api-key", help="Claude API key (required)")
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Claude API key not provided. Use --api-key or set the ANTHROPIC_API_KEY environment variable.")
        return
    
    print(f"Analyzing files in: {args.directory}")
    
    # Get file summaries
    summaries = get_directory_summaries(args.directory)
    print(f"Found {len(summaries)} files to process")
    
    if not summaries:
        print("No files found to rename. Try adding some files to the directory.")
        return
    
    # Get renaming suggestions
    files = create_file_tree(summaries, api_key)
    
    if not files:
        print("Error: Could not get file renaming suggestions.")
        return
    
    # Rename files in place
    rename_files(args.directory, files, args.auto_yes)

if __name__ == "__main__":
    main()
