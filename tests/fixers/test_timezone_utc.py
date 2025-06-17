from __future__ import annotations

import pytest

from django_upgrade.fixers.timezone_utc import fix_django_timezone_utc


@pytest.mark.parametrize(
    "source_code, expected_code",
    [
        # Test case where timezone.utc is used
        (
            "from django.utils import timezone\nprint(timezone.utc)",
            "from datetime import timezone as dt_timezone\nfrom django.utils import timezone\nprint(dt_timezone.utc)",
        ),
        # Test case where datetime.timezone is already imported
        (
            "from django.utils import timezone\nfrom datetime import timezone as dt_timezone\nprint(timezone.utc)",
            "from django.utils import timezone\nfrom datetime import timezone as dt_timezone\nprint(dt_timezone.utc)",
        ),
        # Test case where timezone.utc is not used
        (
            "from django.utils import timezone\nprint('No timezone')",
            "from django.utils import timezone\nprint('No timezone')",
        ),
    ],
)
def test_fix_django_timezone_utc(source_code, expected_code):
    fixed_code, changes_made = fix_django_timezone_utc(source_code)
    assert fixed_code == expected_code
