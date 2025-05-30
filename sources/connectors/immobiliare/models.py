from dataclasses import dataclass
from typing import Optional

@dataclass
class RealEstate:
    """Data model for a real estate property."""
    id: str
    url: str
    contract: str
    agency_id: Optional[str]
    agency_url: Optional[str]
    agency_name: Optional[str]
    is_private_ad: bool
    is_new: bool
    is_luxury: bool
    formatted_price: str
    price: Optional[int]
    bathrooms: Optional[int]
    bedrooms: Optional[int]
    floor: Optional[str]
    formatted_floor: Optional[str]
    total_floors: Optional[int]
    condition: Optional[str]
    rooms: Optional[int]
    has_elevators: bool
    surface: Optional[float]
    surface_formatted: Optional[str]
    type: str
    caption: Optional[str]
    category: str
    description: Optional[str]
    heating_type: Optional[str]
    air_conditioning: Optional[str]
    latitude: float
    longitude: float
    region: str
    province: str
    macrozone: str
    microzone: str
    city: str
    country: str

    @classmethod
    def from_dict(cls, data: dict) -> 'RealEstate':
        """Create a RealEstate instance from a dictionary."""
        return cls(
            id=str(data["realEstate"]["id"]),
            url=data["seo"]["url"],
            contract=data["realEstate"]["contract"],
            agency_id=data["realEstate"]["advertiser"].get("agency", {}).get("label"),
            agency_url=data["realEstate"]["advertiser"].get("agency", {}).get("agencyUrl"),
            agency_name=data["realEstate"]["advertiser"].get("agency", {}).get("displayName"),
            is_private_ad=data["realEstate"]["advertiser"].get("agency") is None,
            is_new=bool(data["realEstate"]["isNew"]),
            is_luxury=bool(data["realEstate"]["luxury"]),
            formatted_price=data["realEstate"]["price"]["formattedValue"],
            price=data["realEstate"]["price"].get("value"),
            bathrooms=data["realEstate"]["properties"][0].get("bathrooms"),
            bedrooms=data["realEstate"]["properties"][0].get("bedRoomsNumber"),
            floor=data["realEstate"]["properties"][0].get("floor", {}).get("abbreviation"),
            formatted_floor=data["realEstate"]["properties"][0].get("floor", {}).get("value"),
            total_floors=data["realEstate"]["properties"][0].get("floors"),
            condition=data["realEstate"]["properties"][0].get("condition"),
            rooms=data["realEstate"]["properties"][0].get("rooms"),
            has_elevators=bool(data["realEstate"]["properties"][0].get("hasElevators")),
            surface=None,  # Will be processed separately
            surface_formatted=data["realEstate"]["properties"][0].get("surface"),
            type=data["realEstate"]["properties"][0]["typologyGA4Translation"],
            caption=data["realEstate"]["properties"][0].get("caption"),
            category=data["realEstate"]["properties"][0]["category"]["name"],
            description=data["realEstate"]["properties"][0].get("description"),
            heating_type=data["realEstate"]["properties"][0].get("energy", {}).get("heatingType"),
            air_conditioning=data["realEstate"]["properties"][0].get("energy", {}).get("airConditioning"),
            latitude=float(data["realEstate"]["properties"][0]["location"]["latitude"]),
            longitude=float(data["realEstate"]["properties"][0]["location"]["longitude"]),
            region=data["realEstate"]["properties"][0]["location"]["region"],
            province=data["realEstate"]["properties"][0]["location"]["province"],
            macrozone=data["realEstate"]["properties"][0]["location"]["macrozone"],
            microzone=data["realEstate"]["properties"][0]["location"]["microzone"],
            city=data["realEstate"]["properties"][0]["location"]["city"],
            country=data["realEstate"]["properties"][0]["location"]["nation"]["id"]
        )

    def to_dict(self) -> dict:
        """Convert the RealEstate instance to a dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "contract": self.contract,
            "agency_id": self.agency_id,
            "agency_url": self.agency_url,
            "agency_name": self.agency_name,
            "is_private_ad": self.is_private_ad,
            "is_new": self.is_new,
            "is_luxury": self.is_luxury,
            "formatted_price": self.formatted_price,
            "price": self.price,
            "bathrooms": self.bathrooms,
            "bedrooms": self.bedrooms,
            "floor": self.floor,
            "formatted_floor": self.formatted_floor,
            "total_floors": self.total_floors,
            "condition": self.condition,
            "rooms": self.rooms,
            "has_elevators": self.has_elevators,
            "surface": self.surface,
            "surface_formatted": self.surface_formatted,
            "type": self.type,
            "caption": self.caption,
            "category": self.category,
            "description": self.description,
            "heating_type": self.heating_type,
            "air_conditioning": self.air_conditioning,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "province": self.province,
            "macrozone": self.macrozone,
            "microzone": self.microzone,
            "city": self.city,
            "country": self.country
        } 