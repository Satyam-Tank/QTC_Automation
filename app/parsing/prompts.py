from app.models.qtc_models import QTCFormData

def get_extraction_prompt(email_context: str) -> str:
    """
    Generates the master prompt for the AI, combining the
    extraction rules (from the PDF) with the raw email context.
    """

    # Get the Pydantic model's JSON schema as a string
    # This tells the AI *exactly* what fields and types to return.
    json_schema = QTCFormData.model_json_schema()

    prompt = f"""
    You are an expert logistics data extraction agent. Your task is to analyze an
    unstructured email for a freight quote request and extract the information
    needed to fill a QTC (Quote-to-Customer) form.

    You MUST return your answer in a valid JSON format that adheres to the
    following JSON Schema:
    
    <JSON_SCHEMA>
    {json_schema}
    </JSON_SCHEMA>

    ---
    EXTRACTION RULES (from QTC v3 Documentation):
    Follow these rules precisely.

    1.  **inquiry_type**:
        - Search for keywords: "budgeting", "costing purpose", "estimation".
        - If found, set to "Budgetary".
        - If not found, default to "Bid to win".

    2.  **client_name**:
        - Extract the company name from the email signature or body.
        - This will be validated against a database later, so get the
          most accurate name (e.g., "ATIQ AL DHAHERI & CO LLC").

    3.  **product**:
        - Keywords "ocean", "sea", "vessel", "FCL", "LCL" -> "Ocean"
        - Keywords "air", "airfreight", "flight" -> "Air"
        - Keywords "road", "truck", "land transport" -> "Road"
        - Keywords "custom clearance", "brokerage", "customs" -> "Brokerage"
        - **Inference**: If container types (20ft, 40HC) are mentioned,
          infer "Ocean".

    4.  **incoterms**:
        - Search for explicit terms: "EXW", "FOB", "FCA", "DAP", "DDP", "CFR", "CIF".
        - **Inference**: If not found, port-to-port language
          (e.g., "Shanghai to Jebel Ali") implies "FOB".
        - If ambiguous, set to "FOB" as a safe default.

    5.  **ocean_type** (if product is "Ocean"):
        - Container units (1x20GP, 2x40HC) -> "FCL"
        - Package/pallet dimensions (1 pallet, 300kg) -> "LCL"
        - "Vehicle" or "car" -> "RORO"
        - "Machinery", "bulk cargo" -> "Break Bulk"

    6.  **containers** (if ocean_type is "FCL"):
        - Parse strings like "2x20ft", "1 x 40HC".
        - Populate a list of objects:
          [ {{"container_type": "20GP", "quantity": 2}},
            {{"container_type": "40HC", "quantity": 1}} ]

    7.  **port_of_loading** & **port_of_discharge**:
        - Extract origin and destination ports/cities.
        - Standardize names (e.g., "Jebel Ali" not "JAFZA").

    8.  **commodity**:
        - **CRITICAL**: This field is mandatory.
        - Find keywords like "Electronics", "Textiles", "General Cargo".
        - If NOT EXPLICITLY STATED, set the value to "NOT_FOUND_HIL".

    9.  **freetime_requirement**:
        - **CRITICAL**: This field is mandatory.
        - Search for patterns: "14 free days", "21 free time".
        - If NOT EXPLICITLY STATED, set the value to "NOT_FOUND_HIL".

    10. **dangerous_goods**:
        - Default to `false`.
        - Set to `true` if email mentions "DG", "hazardous", "IMDG", or
          has an "MSDS" attachment.

    ---
    EMAIL CONTEXT TO ANALYZE:
    This includes the email body and text from all attachments.

    <CONTEXT>
    {email_context}
    </CONTEXT>

    ---
    TASK:
    Analyze the <CONTEXT> using the EXTRACTION RULES and return *only* the
    valid JSON object adhering to the <JSON_SCHEMA>.
    Do not include any other text, greetings, or explanations.
    If a mandatory field (commodity, freetime_requirement) is not found,
    you MUST return "NOT_FOUND_HIL" as its value.
    """
    
    return prompt
