# Import warning suppression immediately when tasks package is imported
from backend.core.suppress_warnings import suppress_third_party_warnings
suppress_third_party_warnings()