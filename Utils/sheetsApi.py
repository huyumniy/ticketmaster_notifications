import requests
import json

def get_data_from_google_sheets(sheet_range, sheet_id):
    """
    Retrieves and formats data from a specified Google Sheet range.
    
    Args:
        sheet_range (str): The cell range to query (e.g., 'A1:H100').
        sheet_id (str): The Google Sheets document ID.
    
    Returns:
        list: A list of rows with columns in the desired order.
              Returns an empty list or None if errors occur.
    """
    # URL parameters
    sheet_title = 'main'
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?sheet={sheet_title}&range={sheet_range}'
    
    # Define the desired column labels in order
    desired_labels = [
        'CATEGORIES', 'QUANTITY', 'PRICE',
        'LINK', 'NAME', 'DATE', 'CITY', "PROXY"
    ]
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None
        
        # Remove wrapping function call (e.g., "/*O_o*/\ngoogle.visualization.Query.setResponse(...)")
        content = response.text
        json_data = content[content.find('(')+1:content.rfind(')')]
        data = json.loads(json_data)
        table = data.get("table", {})
        rows = table.get("rows", [])
        cols = table.get("cols", [])
        if not rows or not cols:
            print("Invalid data format: Missing 'rows' or 'cols'")
            return []
        # print(table)
        # Map column labels to their indices
        col_index = {col['label']: idx for idx, col in enumerate(cols)}
        # Get indices for desired labels (None if not found)
        desired_indices = [col_index.get(label) for label in desired_labels]
        
        formatted_data = []
        for row in rows:
            formatted_row = []
            cells = row.get('c', [])
            for idx in desired_indices:
                if idx is None or idx >= len(cells) or cells[idx] is None:
                    formatted_row.append(None)
                    continue
                
                cell = cells[idx]
                col_type = cols[idx].get('type')
                value = cell.get('v')
                
                if value is None:
                    formatted_row.append(None)
                elif col_type == 'date':
                    # Prefer formatted string if available, else default to str of value
                    formatted_row.append(cell.get('f', str(value)))
                elif col_type == 'number':
                    # Convert float numbers that are integers to int type
                    formatted_row.append(int(value) if isinstance(value, float) and value.is_integer() else value)
                elif col_type == 'string':
                    formatted_row.append(str(value).strip())
                else:
                    formatted_row.append(value)
                    
            formatted_data.append(formatted_row)
        
        return formatted_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    sheet_id = "1hMTAwdquHqyAMUFMRd482Sg_ASqaRsS4UARLcMi4VeM"
    sheet_range = "A1:H"

    response = get_data_from_google_sheets(sheet_range, sheet_id)
    print(response)
