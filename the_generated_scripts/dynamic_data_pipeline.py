# Prompt
"""

Build a dynamic Data Pipeline Parser class named DataPipelineParser.
Requirements:
1. Accept raw JSON strings or List[Dict] objects in initialization.
2. Provide a recursive method to flatten deep nested structures using a '.' delimiter.
3. Build a clean tabular matrix representation matching extracted headers.
4. Clean and parse string representations of nulls (e.g., 'NaN', 'null', 'NA') into true Python None.
5. Compute native statistical aggregates (mean, min, max, sum) column-by-column.
6. DRY Principle Enforced: Do not use impossible numeric array boundary validation paths or copy-pasted loop blocks. Initialize minimum and maximum states based directly on valid numeric tokens.

"""


import json
from typing import Any, Dict, List, Union, Tuple

class DataPipelineParser:
    def __init__(self, data: Union[str, List[Dict[str, Any]]]):
        self._raw_data = self._validate_and_parse_input(data)
        self.headers, self.matrix = self._build_tabular_matrix()
        self.statistics = self._compute_column_statistics()

    def _validate_and_parse_input(self, data: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON string provided: {error}")
            if not isinstance(parsed_data, list):
                raise TypeError("Parsed JSON must represent a list of dictionaries.")
            data = parsed_data
        
        if not isinstance(data, list):
            raise TypeError("Input data must be a JSON string or a List[Dict].")
            
        for row_index, item in enumerate(data):
            if not isinstance(item, dict):
                raise TypeError(f"Item at index {row_index} is not a dictionary.")
                
        return data

    def _clean_value(self, value: Any) -> Any:
        if isinstance(value, str):
            stripped_val = value.strip().lower()
            if stripped_val in {'nan', 'null', 'na', 'none', ''}:
                return None
        return value

    def flatten_nested_structure(self, nested_dict: Dict[str, Any], parent_key: str = '', delimiter: str = '.') -> Dict[str, Any]:
        if not isinstance(nested_dict, dict):
            raise TypeError("flatten_nested_structure expects a dictionary.")
            
        flattened_items = {}
        for key, value in nested_dict.items():
            new_key = f"{parent_key}{delimiter}{key}" if parent_key else key
            if isinstance(value, dict):
                flattened_items.update(self.flatten_nested_structure(value, new_key, delimiter))
            else:
                flattened_items[new_key] = self._clean_value(value)
        return flattened_items

    def _build_tabular_matrix(self) -> Tuple[List[str], List[List[Any]]]:
        flattened_records = [self.flatten_nested_structure(record) for record in self._raw_data]
        
        headers = []
        seen_headers = set()
        for record in flattened_records:
            for key in record.keys():
                if key not in seen_headers:
                    headers.append(key)
                    seen_headers.add(key)
                    
        matrix = []
        for record in flattened_records:
            row = [record.get(header) for header in headers]
            matrix.append(row)
            
        return headers, matrix

    def _compute_column_statistics(self) -> Dict[str, Dict[str, Union[float, None]]]:
        statistics = {}
        total_columns = len(self.headers)
        
        for col_idx in range(total_columns):
            header = self.headers[col_idx]
            
            valid_numbers = []
            for row in self.matrix:
                if col_idx < 0 or col_idx >= len(row):
                    continue
                val = row[col_idx]
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    valid_numbers.append(val)
                    
            num_valid = len(valid_numbers)
            if num_valid <= 0:
                statistics[header] = {"mean": None, "min": None, "max": None, "sum": None}
                continue
                
            col_min = valid_numbers[0]
            col_max = valid_numbers[0]
            col_sum = 0.0
            
            for i in range(num_valid):
                num = valid_numbers[i]
                if num < col_min:
                    col_min = num
                if num > col_max:
                    col_max = num
                col_sum += num
                
            col_mean = col_sum / num_valid
            
            statistics[header] = {
                "mean": col_mean,
                "min": col_min,
                "max": col_max,
                "sum": col_sum
            }
            
        return statistics