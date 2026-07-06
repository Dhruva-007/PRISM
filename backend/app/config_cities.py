"""
City configuration for PRISM.

Centralizes all city-specific data including coordinates, districts,
health data profiles, and construction site information.

To add a new city, add a new entry to CITY_CONFIGS.
All adapters and services read from this configuration.
"""

from dataclasses import dataclass, field


@dataclass
class DistrictConfig:
    """A district within a city for health data simulation."""

    name: str
    lat_offset: float
    lon_offset: float


@dataclass
class ConstructionSiteConfig:
    """A construction site within a city."""

    name: str
    lat_offset: float
    lon_offset: float
    district: str
    activity: str
    proximity_schools: float
    proximity_hospitals: float
    radius_m: float
    duration_days: int


@dataclass
class CityConfig:
    """Complete configuration for a supported city."""

    city_id: str
    display_name: str
    state: str
    country: str
    latitude: float
    longitude: float
    map_zoom: int
    districts: list[DistrictConfig] = field(default_factory=list)
    construction_sites: list[ConstructionSiteConfig] = field(default_factory=list)
    health_conditions: list[str] = field(default_factory=list)


CITY_CONFIGS: dict[str, CityConfig] = {
    "hyderabad": CityConfig(
        city_id="hyderabad",
        display_name="Hyderabad",
        state="Telangana",
        country="India",
        latitude=17.3850,
        longitude=78.4867,
        map_zoom=12,
        districts=[
            DistrictConfig("Secunderabad", 0.0, 0.0),
            DistrictConfig("Banjara Hills", -0.012, -0.018),
            DistrictConfig("Old City - Charminar", -0.020, 0.008),
            DistrictConfig("Kukatpally", 0.018, -0.025),
            DistrictConfig("LB Nagar", -0.008, 0.030),
            DistrictConfig("Uppal Industrial Area", 0.005, 0.035),
            DistrictConfig("Madhapur - HITEC City", -0.005, -0.035),
        ],
        construction_sites=[
            ConstructionSiteConfig(
                name="Hyderabad Metro Rail — Phase 2 Extension",
                lat_offset=0.018,
                lon_offset=-0.022,
                district="Kukatpally",
                activity="Tunnel boring and elevated corridor construction",
                proximity_schools=280,
                proximity_hospitals=950,
                radius_m=800,
                duration_days=540,
            ),
            ConstructionSiteConfig(
                name="Outer Ring Road Junction Flyover",
                lat_offset=-0.025,
                lon_offset=0.040,
                district="Uppal Industrial Area",
                activity="Elevated road construction and pile driving",
                proximity_schools=420,
                proximity_hospitals=1800,
                radius_m=600,
                duration_days=365,
            ),
            ConstructionSiteConfig(
                name="Charminar Heritage Zone Restoration",
                lat_offset=-0.022,
                lon_offset=0.010,
                district="Old City - Charminar",
                activity="Demolition and road widening",
                proximity_schools=150,
                proximity_hospitals=500,
                radius_m=400,
                duration_days=180,
            ),
            ConstructionSiteConfig(
                name="HITEC City IT Corridor Expansion",
                lat_offset=-0.008,
                lon_offset=-0.038,
                district="Madhapur - HITEC City",
                activity="Foundation and high-rise structural work",
                proximity_schools=680,
                proximity_hospitals=1200,
                radius_m=350,
                duration_days=720,
            ),
            ConstructionSiteConfig(
                name="Secunderabad Railway Station Redevelopment",
                lat_offset=0.002,
                lon_offset=0.005,
                district="Secunderabad",
                activity="Station demolition and reconstruction",
                proximity_schools=320,
                proximity_hospitals=750,
                radius_m=500,
                duration_days=480,
            ),
        ],
        health_conditions=[
            "Acute respiratory infection",
            "Asthma exacerbation",
            "Dust-induced bronchitis",
            "Allergic rhinitis — construction dust",
            "COPD exacerbation",
            "Heat-induced respiratory distress",
            "Silicosis risk — industrial workers",
        ],
    ),
    "delhi": CityConfig(
        city_id="delhi",
        display_name="Delhi",
        state="NCT",
        country="India",
        latitude=28.6139,
        longitude=77.2090,
        map_zoom=11,
        districts=[
            DistrictConfig("Connaught Place", 0.0, 0.0),
            DistrictConfig("Anand Vihar", 0.015, 0.025),
            DistrictConfig("Dwarka", -0.020, -0.040),
            DistrictConfig("Rohini", 0.030, -0.015),
            DistrictConfig("Saket", -0.015, 0.005),
            DistrictConfig("Mayapuri Industrial", 0.005, -0.025),
            DistrictConfig("Okhla Industrial Area", -0.025, 0.020),
            DistrictConfig("Mundka", 0.025, -0.045),
        ],
        construction_sites=[
            ConstructionSiteConfig(
                name="Delhi Metro Phase 4 — Aerocity Extension",
                lat_offset=-0.020,
                lon_offset=-0.030,
                district="Dwarka",
                activity="Underground tunnel boring and station excavation",
                proximity_schools=200,
                proximity_hospitals=800,
                radius_m=900,
                duration_days=720,
            ),
            ConstructionSiteConfig(
                name="Pragati Maidan Redevelopment",
                lat_offset=0.002,
                lon_offset=0.012,
                district="Connaught Place",
                activity="Large-scale demolition and reconstruction",
                proximity_schools=450,
                proximity_hospitals=600,
                radius_m=700,
                duration_days=540,
            ),
            ConstructionSiteConfig(
                name="Barapullah Elevated Corridor Phase 3",
                lat_offset=-0.010,
                lon_offset=0.008,
                district="Saket",
                activity="Elevated highway construction and pile driving",
                proximity_schools=350,
                proximity_hospitals=1100,
                radius_m=500,
                duration_days=365,
            ),
            ConstructionSiteConfig(
                name="Dwarka Expressway Final Phase",
                lat_offset=-0.025,
                lon_offset=-0.055,
                district="Dwarka",
                activity="Road construction and land clearing",
                proximity_schools=600,
                proximity_hospitals=2000,
                radius_m=1200,
                duration_days=480,
            ),
        ],
        health_conditions=[
            "Acute respiratory infection",
            "Severe asthma exacerbation",
            "Chronic bronchitis — pollution",
            "Allergic rhinitis",
            "COPD exacerbation",
            "Stubble burning smoke inhalation",
            "Pneumonia — particulate exposure",
        ],
    ),
    "bangalore": CityConfig(
        city_id="bangalore",
        display_name="Bangalore",
        state="Karnataka",
        country="India",
        latitude=12.9716,
        longitude=77.5946,
        map_zoom=12,
        districts=[
            DistrictConfig("Majestic - City Centre", 0.0, 0.0),
            DistrictConfig("Whitefield", 0.005, 0.055),
            DistrictConfig("Electronic City", -0.030, 0.015),
            DistrictConfig("Yelahanka", 0.035, -0.005),
            DistrictConfig("Jayanagar", -0.015, -0.008),
            DistrictConfig("Peenya Industrial", 0.022, -0.022),
            DistrictConfig("Hebbal", 0.025, 0.010),
        ],
        construction_sites=[
            ConstructionSiteConfig(
                name="Namma Metro — Yellow Line Extension",
                lat_offset=0.005,
                lon_offset=0.050,
                district="Whitefield",
                activity="Elevated metro corridor construction",
                proximity_schools=300,
                proximity_hospitals=1100,
                radius_m=700,
                duration_days=600,
            ),
            ConstructionSiteConfig(
                name="Peripheral Ring Road — North Sector",
                lat_offset=0.035,
                lon_offset=-0.010,
                district="Yelahanka",
                activity="Road construction and land acquisition demolition",
                proximity_schools=500,
                proximity_hospitals=1500,
                radius_m=1000,
                duration_days=720,
            ),
            ConstructionSiteConfig(
                name="Hebbal Flyover Expansion",
                lat_offset=0.025,
                lon_offset=0.008,
                district="Hebbal",
                activity="Flyover widening and pile driving",
                proximity_schools=380,
                proximity_hospitals=900,
                radius_m=450,
                duration_days=240,
            ),
            ConstructionSiteConfig(
                name="Electronic City Elevated Expressway",
                lat_offset=-0.032,
                lon_offset=0.018,
                district="Electronic City",
                activity="Expressway elevation and foundation work",
                proximity_schools=700,
                proximity_hospitals=1800,
                radius_m=600,
                duration_days=540,
            ),
        ],
        health_conditions=[
            "Acute respiratory infection",
            "Asthma exacerbation",
            "Allergic rhinitis — dust and pollen",
            "COPD exacerbation",
            "Traffic pollution bronchitis",
            "Construction dust silicosis risk",
        ],
    ),
    "mumbai": CityConfig(
        city_id="mumbai",
        display_name="Mumbai",
        state="Maharashtra",
        country="India",
        latitude=19.0760,
        longitude=72.8777,
        map_zoom=12,
        districts=[
            DistrictConfig("Colaba - South Mumbai", 0.0, 0.0),
            DistrictConfig("Andheri", 0.040, -0.015),
            DistrictConfig("Bandra", 0.025, -0.005),
            DistrictConfig("Kurla", 0.035, 0.010),
            DistrictConfig("Dharavi", 0.028, 0.005),
            DistrictConfig("Navi Mumbai", 0.020, 0.040),
            DistrictConfig("Thane Industrial Belt", 0.055, 0.018),
        ],
        construction_sites=[
            ConstructionSiteConfig(
                name="Mumbai Metro Line 3 — Colaba-Bandra-SEEPZ",
                lat_offset=0.015,
                lon_offset=-0.008,
                district="Bandra",
                activity="Underground tunnel boring in dense urban area",
                proximity_schools=150,
                proximity_hospitals=400,
                radius_m=600,
                duration_days=720,
            ),
            ConstructionSiteConfig(
                name="Coastal Road Project — South Mumbai",
                lat_offset=0.008,
                lon_offset=-0.005,
                district="Colaba - South Mumbai",
                activity="Coastal reclamation and road construction",
                proximity_schools=500,
                proximity_hospitals=800,
                radius_m=900,
                duration_days=540,
            ),
            ConstructionSiteConfig(
                name="Mumbai Trans Harbour Link (Atal Setu Extension)",
                lat_offset=0.018,
                lon_offset=0.035,
                district="Navi Mumbai",
                activity="Bridge construction and approach road",
                proximity_schools=800,
                proximity_hospitals=2200,
                radius_m=1500,
                duration_days=480,
            ),
            ConstructionSiteConfig(
                name="Dharavi Redevelopment Project",
                lat_offset=0.028,
                lon_offset=0.006,
                district="Dharavi",
                activity="Large-scale demolition and high-rise construction",
                proximity_schools=100,
                proximity_hospitals=350,
                radius_m=800,
                duration_days=1080,
            ),
        ],
        health_conditions=[
            "Acute respiratory infection",
            "Asthma exacerbation",
            "Monsoon-related respiratory illness",
            "Industrial pollution bronchitis",
            "COPD exacerbation",
            "Coastal humidity respiratory distress",
            "Dust-induced allergic rhinitis",
        ],
    ),
}

DEFAULT_CITY = "hyderabad"

SUPPORTED_CITY_IDS = list(CITY_CONFIGS.keys())


def get_city_config(city_id: str) -> CityConfig:
    """
    Get configuration for a city by ID.

    Falls back to default city if ID not found.
    """
    return CITY_CONFIGS.get(city_id.lower(), CITY_CONFIGS[DEFAULT_CITY])


def get_all_city_summaries() -> list[dict]:
    """Return a summary list of all supported cities for the frontend."""
    return [
        {
            "city_id": c.city_id,
            "display_name": c.display_name,
            "state": c.state,
            "country": c.country,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "map_zoom": c.map_zoom,
            "district_count": len(c.districts),
            "construction_sites": len(c.construction_sites),
        }
        for c in CITY_CONFIGS.values()
    ]