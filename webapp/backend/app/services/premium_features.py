"""
Premium Features Service for BIN Search Pro
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
import csv
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random

from app.models import User, UserTier, BinData, UsageLog, ActionType, Subscription, SubscriptionStatus
from app.services.card_generator import (
    validate_bin, create_card_number, generate_cvv, 
    AVS_POSTAL_CODES, get_card_length
)

class PremiumFeaturesService:
    """Service for managing premium features."""
    
    def __init__(self):
        self.premium_tiers = [UserTier.PREMIUM, UserTier.API]
    
    def is_user_premium(self, user: Optional[User], db: Session) -> bool:
        """Check if user has active premium subscription."""
        if not user:
            return False
        
        # For now, just check tier (can add subscription checks later)
        return user.tier in [tier.value for tier in self.premium_tiers]
    
    def get_rate_limits(self, user: Optional[User], db: Session) -> Dict[str, int]:
        """Get rate limits based on user tier."""
        if user and self.is_user_premium(user, db):
            return {
                "card_generation": 1000,
                "bin_lookup": 10000,
                "bulk_generation": 100,
                "export": 50,
                "avs_generation": 1000
            }
        else:
            return {
                "card_generation": 5,
                "bin_lookup": 10,
                "bulk_generation": 0,
                "export": 0,
                "avs_generation": 0
            }
    
    async def enhanced_bin_lookup(
        self, 
        bin_input: str, 
        user: Optional[User], 
        db: Session,
        include_extended_data: bool = False
    ) -> Dict[str, Any]:
        """Enhanced BIN lookup with premium features."""
        is_valid, message, bin_data = validate_bin(bin_input, db)
        if not is_valid:
            return {"error": message, "valid": False}
        
        response = {
            "bin": bin_data.bin,
            "brand": bin_data.brand,
            "issuer": bin_data.issuer,
            "type": bin_data.type,
            "level": bin_data.level,
            "country_code": bin_data.country_code,
            "country_name": bin_data.country_name,
            "bank_phone": bin_data.bank_phone,
            "bank_url": bin_data.bank_url,
            "valid": True,
            "lookup_time": datetime.utcnow().isoformat()
        }
        
        if self.is_user_premium(user, db) and include_extended_data:
            response["premium"] = True
        
        return response
    
    async def generate_card_with_avs(
        self,
        bin_input: str,
        country_code: str,
        user: User,
        db: Session,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """Generate cards with AVS postal codes."""
        if not self.is_user_premium(user, db):
            raise ValueError("AVS generation requires premium subscription")
        
        if country_code.upper() not in AVS_POSTAL_CODES:
            raise ValueError(f"AVS not supported for {country_code}")
        
        is_valid, message, bin_data = validate_bin(bin_input, db)
        if not is_valid:
            raise ValueError(message)
        
        cards = []
        postal_codes = AVS_POSTAL_CODES[country_code.upper()]
        
        for _ in range(count):
            card_number = create_card_number(bin_input, bin_data)
            current_year = datetime.now().year
            exp_year = random.randint(current_year + 1, current_year + 8)
            exp_month = random.randint(1, 12)
            expiry = f"{exp_month:02d}/{str(exp_year)[2:]}"
            cvv = generate_cvv(card_number, expiry, seed=True)
            postal_code = random.choice(postal_codes)
            
            card_info = {
                "number": card_number,
                "cvv": cvv,
                "expiry": expiry,
                "postal_code": postal_code,
                "country_code": country_code.upper(),
                "bin": bin_input,
                "brand": bin_data.brand,
                "issuer": bin_data.issuer,
                "type": bin_data.type,
                "country": bin_data.country_name,
                "generated_at": datetime.utcnow().isoformat(),
                "avs_enabled": True
            }
            
            cards.append(card_info)
        
        return cards
    
    def export_cards_json(self, cards: List[Dict[str, Any]]) -> str:
        """Export cards in JSON format."""
        return json.dumps({
            "cards": cards,
            "export_format": "json",
            "exported_at": datetime.utcnow().isoformat(),
            "count": len(cards)
        }, indent=2)
    
    def export_cards_csv(self, cards: List[Dict[str, Any]]) -> str:
        """Export cards in CSV format."""
        if not cards:
            return "No cards to export"
        
        output = io.StringIO()
        fieldnames = cards[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for card in cards:
            writer.writerow(card)
        
        return output.getvalue()
    
    def export_cards_xml(self, cards: List[Dict[str, Any]]) -> str:
        """Export cards in XML format."""
        root = ET.Element("cards")
        root.set("count", str(len(cards)))
        root.set("exported_at", datetime.utcnow().isoformat())
        
        for card in cards:
            card_element = ET.SubElement(root, "card")
            for key, value in card.items():
                elem = ET.SubElement(card_element, key)
                elem.text = str(value) if value is not None else ""
        
        rough_string = ET.tostring(root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def export_cards(
        self, 
        cards: List[Dict[str, Any]], 
        export_format: str = "json"
    ) -> str:
        """Export cards in specified format."""
        export_format = export_format.lower()
        
        if export_format == "json":
            return self.export_cards_json(cards)
        elif export_format == "csv":
            return self.export_cards_csv(cards)
        elif export_format == "xml":
            return self.export_cards_xml(cards)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

# Global instance
premium_service = PremiumFeaturesService()