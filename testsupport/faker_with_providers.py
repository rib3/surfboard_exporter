from faker import Faker

from testsupport.surfboard_provider import SurfboardProvider


class FakerWithProviders(Faker, SurfboardProvider):
    """Annotation-only Faker."""
