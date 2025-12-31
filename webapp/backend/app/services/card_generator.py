import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import BinData, BlockedBin
from app.database import get_redis

# Test BINs to block (from your existing bot)
TEST_BINS = {
    "411111", "555555", "378282", "378734", "371449",
    "601111", "630495", "630490", "360000", "305693",
    "385200", "601100", "353011", "356600"
}

# AVS postal codes by country (from your existing bot)
AVS_POSTAL_CODES = {
    "US": ["10001", "90210", "60601", "94102", "33101"],  # NYC, LA, Chicago, SF, Miami
    "IT": ["00100", "20100", "80100", "40100", "50100"],  # Rome, Milan, Naples, Bologna, Florence
    "GB": ["SW1A 1AA", "M1 1AA", "B1 1AA", "L1 1AA", "CF1 1AA"],  # London, Manchester, Birmingham, Liverpool, Cardiff
    "CA": ["M5H 2N2", "V6B 1A1", "T2P 1J9", "H2Y 1A6", "K1A 0A6"],  # Toronto, Vancouver, Calgary, Montreal, Ottawa
    "AU": ["2000", "3000", "4000", "5000", "6000"],  # Sydney, Melbourne, Brisbane, Adelaide, Perth
    "DE": ["10115", "20095", "80331", "50667", "01067"],  # Berlin, Hamburg, Munich, Cologne, Dresden
    "FR": ["75001", "69001", "13001", "31000", "59000"]   # Paris, Lyon, Marseille, Toulouse, Lille
}

def validate_bin(bin_input: str, db: Session) -> Tuple[bool, str, Optional[BinData]]:
    """
    Validate BIN against database and blocked BINs.
    Returns (is_valid, message, bin_data)
    """
    # Clean input
    bin_str = str(bin_input).strip()
    
    # Check length
    if len(bin_str) < 6:
        return False, "BIN must be at least 6 digits", None
    
    # Take first 6 digits
    bin_prefix = bin_str[:6]
    
    # Check if blocked (test BIN)
    if bin_prefix in TEST_BINS:
        return False, "Test BIN blocked - use production BINs only", None
    
    # Check database blocked list
    blocked = db.query(BlockedBin).filter(BlockedBin.bin == bin_prefix).first()
    if blocked:
        return False, f"BIN blocked: {blocked.reason}", None
    
    # Look up in database
    bin_data = db.query(BinData).filter(BinData.bin == bin_prefix).first()
    if not bin_data:
        return False, "BIN not found in database", None
    
    return True, "Valid BIN", bin_data

def get_card_length(brand: str, card_type: Optional[str] = None) -> int:
    """
    Get appropriate card length based on brand and type.
    """
    brand_upper = brand.upper() if brand else ""
    
    if "AMERICAN EXPRESS" in brand_upper or "AMEX" in brand_upper:
        return 15
    elif "DINERS" in brand_upper:
        return random.choice([14, 16])
    elif "DISCOVER" in brand_upper:
        return random.choice([16, 19])
    elif card_type and "PREPAID" in card_type.upper():
        return 16
    else:
        return 16  # Default for Visa, Mastercard, etc.

def luhn_checksum(card_number: str) -> bool:
    """
    Validate card number using Luhn algorithm.
    """
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    
    return checksum % 10 == 0

def create_card_number(bin_prefix: str, bin_info: BinData = None) -> str:
    """
    Create enhanced card number with weighted algorithm.
    """
    # Determine card length
    brand = bin_info.brand if bin_info else ""
    card_type = bin_info.type if bin_info else ""
    target_length = get_card_length(brand, card_type)
    
    # Start with BIN prefix
    bin_len = len(bin_prefix)
    remaining_digits = target_length - bin_len - 1  # -1 for check digit
    
    # Weighted digit generation (favors 0-5)
    weights = [2, 2, 2, 2, 2, 2, 1, 1, 1, 1]  # 0-5 have weight 2, 6-9 have weight 1
    digit_choices = list(range(10))
    
    max_attempts = 100
    for _ in range(max_attempts):
        # Generate random digits with weighted distribution
        random_digits = []
        digit_counts = {i: 0 for _ in range(10)}
        
        for _ in range(remaining_digits):
            digit = random.choices(digit_choices, weights=weights)[0]
            # Limit each digit to max 2 occurrences
            if digit_counts[digit] < 2:
                random_digits.append(digit)
                digit_counts[digit] += 1
            else:
                # Find alternative digit
                alternatives = [d for d in digit_choices if digit_counts[d] < 2]
                if alternatives:
                    alt_digit = random.choices(alternatives, 
                                             weights=[weights[d] for d in alternatives])[0]
                    random_digits.append(alt_digit)
                    digit_counts[alt_digit] += 1
                else:
                    random_digits.append(random.choice(digit_choices))
        
        # Create number without check digit
        partial_number = bin_prefix + ''.join(map(str, random_digits))
        
        # Advanced pattern filtering
        digit_str = ''.join(map(str, random_digits))
        
        # Check for 3 consecutive identical digits
        has_three_identical = any(
            digit_str[i] == digit_str[i+1] == digit_str[i+2]
            for _ in range(len(digit_str) - 2)
        )
        
        # Check for 3 consecutive ascending
        has_ascending = any(
            int(digit_str[i]) + 1 == int(digit_str[i+1]) and 
            int(digit_str[i+1]) + 1 == int(digit_str[i+2])
            for _ in range(len(digit_str) - 2)
        )
        
        # Check for 3 consecutive descending
        has_descending = any(
            int(digit_str[i]) - 1 == int(digit_str[i+1]) and 
            int(digit_str[i+1]) - 1 == int(digit_str[i+2])
            for _ in range(len(digit_str) - 2)
        )
        
        # If patterns are acceptable, calculate check digit
        if not (has_three_identical or has_ascending or has_descending):
            # Calculate Luhn check digit
            for check_digit in range(10):
                full_number = partial_number + str(check_digit)
                if luhn_checksum(full_number):
                    return full_number
    
    # Fallback: simple random generation if advanced fails
    remaining_digits = target_length - bin_len - 1
    random_part = ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
    partial_number = bin_prefix + random_part
    
    for check_digit in range(10):
        full_number = partial_number + str(check_digit)
        if luhn_checksum(full_number):
            return full_number
    
    return partial_number + "0"  # Final fallback

def generate_cvv(card_number: str, expiry: Optional[str] = None, seed: bool = True) -> str:
    """
    Generate CVV with optional seeding.
    """
    # Determine CVV length based on card number
    if card_number.startswith(('34', '37')):  # American Express
        cvv_length = 4
    else:
        cvv_length = 3
    
    if seed and expiry:
        # Seeded CVV using SHA256
        seed_string = f"{card_number}{expiry}"
        hash_digest = hashlib.sha256(seed_string.encode()).hexdigest()
        # Use first digits of hash for CVV
        cvv = ''.join([c for c in hash_digest if c.isdigit()])[:cvv_length]
        if len(cvv) == cvv_length:
            return cvv
    
    # Fallback to random generation
    return ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])

def generate_expiry(card_type: Optional[str] = None) -> str:
    """
    Generate realistic expiry date based on card type.
    """
    current_date = datetime.now()
    
    # Determine expiry range based on card type
    if card_type and "PREPAID" in card_type.upper():
        # Prepaid cards: 1-2 years
        months_to_add = random.randint(12, 24)
    else:
        # Regular cards: 3-5 years
        months_to_add = random.randint(36, 60)
    
    expiry_date = current_date + timedelta(days=months_to_add * 30)
    return expiry_date.strftime("%m/%Y")

def generate_avs_postal_code(country_code: str) -> Optional[str]:
    """
    Generate realistic postal code for AVS testing.
    """
    if country_code.upper() in AVS_POSTAL_CODES:
        return random.choice(AVS_POSTAL_CODES[country_code.upper()])
    return None

def format_card_display(number: str, cvv: str, expiry: str, bin_info: BinData = None, postal_code: Optional[str] = None) -> Dict:
    """
    Format card information for display.
    """
    # Format card number with spaces
    if len(number) == 15:  # American Express
        formatted_number = f"{number[:4]} {number[4:10]} {number[10:]}"
    else:  # 16+ digit cards
        formatted_number = ' '.join([number[i:i+4] for _ in range(0, len(number), 4)])
    
    card_data = {
        "number": formatted_number,
        "cvv": cvv,
        "expiry": expiry,
        "bin": number[:6] if len(number) >= 6 else number,
    }
    
    if bin_info:
        card_data.update({
            "brand": bin_info.brand,
            "issuer": bin_info.issuer,
            "type": bin_info.type,
            "country": bin_info.country_name,
            "country_code": bin_info.country_code
        })
    
    if postal_code:
        card_data["postal_code"] = postal_code
    
    return card_data

async def generate_test_card(
    bin_input: str, 
    db: Session, 
    include_avs: bool = False, 
    avs_country: Optional[str] = None
) -> Dict:
    """
    Generate a complete test card with all enhanced features.
    """
    # Validate BIN
    is_valid, message, bin_data = validate_bin(bin_input, db)
    if not is_valid:
        raise ValueError(message)
    
    # Generate card components
    card_number = create_card_number(bin_input, bin_data)
    expiry = generate_expiry(bin_data.type if bin_data else None)
    cvv = generate_cvv(card_number, expiry, seed=True)
    
    # Generate postal code if AVS requested
    postal_code = None
    if include_avs and avs_country:
        postal_code = generate_avs_postal_code(avs_country)
        if not postal_code:
            raise ValueError(f"AVS not supported for country: {avs_country}")
    
    # Format and return card data
    return format_card_display(card_number, cvv, expiry, bin_data, postal_code)
