# Matchway Spots: pickup points at college entrances in Pune (shown as the M logo + college name).
# To add a college, add one line: (id, college name, latitude, longitude).
# NOTE: these coordinates are approximate (campus gate area). Check the pins
# on the map and fix any that sit in the wrong place.

PUNE_COLLEGE_SPOTS = [
    ("pune_coep", "COEP Technological University", 18.5292, 73.8567),
    ("pune_fergusson", "Fergusson College", 18.5235, 73.8410),
    ("pune_sppu", "Savitribai Phule Pune University", 18.5525, 73.8240),
    ("pune_modern", "Modern College, Shivajinagar", 18.5303, 73.8467),
    ("pune_bmcc", "BMCC (Brihan Maharashtra College of Commerce)", 18.5145, 73.8385),
    ("pune_garware", "Abasaheb Garware College", 18.5122, 73.8310),
    ("pune_ils", "ILS Law College", 18.5154, 73.8304),
    ("pune_aissms", "AISSMS College of Engineering", 18.5313, 73.8749),
    ("pune_wadia", "Nowrosjee Wadia College", 18.5298, 73.8740),
    ("pune_bj", "BJ Medical College", 18.5278, 73.8703),
    ("pune_mitwpu", "MIT World Peace University, Kothrud", 18.4968, 73.8076),
    ("pune_cummins", "Cummins College of Engineering for Women", 18.4906, 73.8223),
    ("pune_vit", "Vishwakarma Institute of Technology, Bibwewadi", 18.4637, 73.8681),
    ("pune_pict", "PICT, Dhankawadi", 18.4574, 73.8508),
    ("pune_bvcoe", "Bharati Vidyapeeth College of Engineering", 18.4569, 73.8540),
    ("pune_siu", "Symbiosis International University, Viman Nagar", 18.5718, 73.9138),
    ("pune_sit", "Symbiosis Institute of Technology, Lavale", 18.5400, 73.7289),
    ("pune_ait", "Army Institute of Technology, Dighi", 18.6035, 73.8697),
    ("pune_dypakurdi", "DY Patil College of Engineering, Akurdi", 18.6486, 73.7698),
    ("pune_pccoe", "PCCOE, Nigdi", 18.6523, 73.7716),
]


def seed_spots(spot_service):
    """Adds the college spots to the spot service (skips ones already there)."""
    added = 0
    for spot_id, college, lat, lon in PUNE_COLLEGE_SPOTS:
        try:
            spot_service.add_spot(spot_id, college, lat, lon)
            added += 1
        except ValueError:
            pass  # already exists
    return added
