import gsbg
import os

# --- Configuration ---
# Your Google Scholar profile link
profile_link = "https://scholar.google.co.uk/citations?user=LZmZFtMAAAAJ&hl=en"

# Where to save the badge
save_path = "badges"

# The name of the badge file
svg_name = "google_scholar_citations.svg"
# ---------------------

print(f"Generating badge for: {profile_link}")

# Ensure the save directory exists
os.makedirs(save_path, exist_ok=True)

# Generate the badge
try:
    gsbg.gene_citation_badge_svg(
        link=profile_link,
        link_type="profile",
        svg_name=svg_name,
        path_to_save=save_path,
    )
    print(f"Successfully generated badge at: {save_path}/{svg_name}")
except Exception as e:
    print(f"Error generating badge: {e}")
