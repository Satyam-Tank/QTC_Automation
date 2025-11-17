import re
from bs4 import BeautifulSoup
from html import unescape
from typing import Dict, Any, List

def parse_full_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses the full email data from Microsoft Graph API response.
    """
    result: Dict[str, Any] = {
        'sender': None,
        'recipients': [],
        'cc_recipients': [],
        'subject': None,
        'table_data': {}
    }
    
    try:
        if 'from' in email_data and email_data['from']:
            sender_info = email_data['from'].get('emailAddress', {})
            result['sender'] = {
                'name': sender_info.get('name', ''),
                'email': sender_info.get('address', '')
            }
        
        if 'toRecipients' in email_data:
            for recipient in email_data['toRecipients']:
                recipient_info = recipient.get('emailAddress', {})
                result['recipients'].append({
                    'name': recipient_info.get('name', ''),
                    'email': recipient_info.get('address', '')
                })
        
        if 'ccRecipients' in email_data:
            for cc_recipient in email_data['ccRecipients']:
                cc_info = cc_recipient.get('emailAddress', {})
                result['cc_recipients'].append({
                    'name': cc_info.get('name', ''),
                    'email': cc_info.get('address', '')
                })
        
        result['subject'] = email_data.get('subject', '')
        
        html_body = email_data.get('body', {}).get('content', '')
        
        if html_body:
            result['table_data'] = parse_key_value_table(html_body)
        
    except Exception as e:
        print(f"Error parsing email data: {e}")
    
    return result

def parse_key_value_table(html_content: str) -> Dict[str, str]:
    """
    Parses the key-value table from the HTML content of the email.
    """
    if not html_content:
        return {}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    main_table = None
    for table in tables:
        headers = table.find_all(['th', 'td'])
        header_text = ' '.join([h.get_text(strip=True).lower() for h in headers[:4]])
        
        if 'description' in header_text and 'values' in header_text:
            main_table = table
            break
    
    if not main_table:
        if not tables:
            return {}
        main_table = max(tables, key=lambda t: len(t.find_all('tr')), default=None)
    
    if not main_table:
        return {}
    
    data: Dict[str, str] = {}
    rows = main_table.find_all('tr')
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        
        if len(cells) >= 2:
            key_cell = cells[0]
            value_cell = cells[1]
            
            key = clean_text(key_cell.get_text(strip=True))
            value = clean_text(value_cell.get_text(strip=True))
            
            if key and key.lower() not in ['description', 'values']:
                data[key] = value
    
    return data

def clean_text(text: str) -> str:
    """Cleans and normalizes text content."""
    if not text:
        return ''
    
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_dimensions_and_weight(cargo_details: str) -> Dict[str, str]:
    """
    Extracts dimensions and weight information from cargo details string.
    """
    result: Dict[str, str] = {
        'length': '', 'width': '', 'height': '',
        'num_packages': '', 'volume_weight': '', 'gross_weight': ''
    }
    
    if not cargo_details:
        return result
    
    dimension_pattern = r'(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)\s*cm'
    dimension_match = re.search(dimension_pattern, cargo_details)
    
    if dimension_match:
        result['length'] = dimension_match.group(1)
        result['width'] = dimension_match.group(2)
        result['height'] = dimension_match.group(3)
        
        try:
            l, w, h = int(result['length']), int(result['width']), int(result['height'])
            volume_weight = (l * w * h) / 6000
            result['volume_weight'] = f"{volume_weight:.2f}"
        except ValueError:
            pass
    
    pallet_pattern = r'(?:No of Pallet|packages?)\s*:?\s*(\d+)'
    pallet_match = re.search(pallet_pattern, cargo_details, re.IGNORECASE)
    if pallet_match:
        result['num_packages'] = pallet_match.group(1)
    
    weight_pattern = r'(?:Total Weight|Weight)\s*:?\s*(\d+(?:\.\d+)?)'
    weight_match = re.search(weight_pattern, cargo_details, re.IGNORECASE)
    if weight_match:
        result['gross_weight'] = weight_match.group(1)
    
    return result
