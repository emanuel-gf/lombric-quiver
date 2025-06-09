def cacheb_key():
    """
    Request and validate the cacheb key for Earth Hub service access.
    
    Returns:
        str: The validated cacheb key
    """
    try:
        key = str(input("Please enter your cacheb key to access the Earth Hub service: ")).strip()
        
        if not key:
            raise ValueError("Key cannot be empty")
            
        return key
        
    except KeyboardInterrupt:
        print("\nKey input cancelled by user")
        return None
    except Exception as e:
        print(f"Error getting key: {e}")
        return None