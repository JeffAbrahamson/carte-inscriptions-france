#!/usr/bin/env python

import re
import unicodedata

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import pandas as pd


def normalise_name(name_str):
    """Lowercase, strip, remove accents, and normalize spaces/hyphens."""
    name_str = name_str.lower().strip()
    name_str = unicodedata.normalize("NFD", name_str)
    name_str = "".join(
        c for c in name_str if unicodedata.category(c) != "Mn"
    )  # remove accents
    name_str = re.sub(
        r"[-\s]+", " ", name_str
    )  # replace hyphens and multiple spaces with single space
    return name_str


def load_commune_data(csv_path="communesdefrancev2.csv"):
    """Load a CSV of postal codes and geo coordinates.

    The file must at least contain columns 'code_postal', 'latitude',
    'longitude' columns.

    The file in this directory came from data.gouv.fr, modified only
    for column names (s/ /_/g; and downcasing) and converting line
    endings (DOS to unix).

    """
    df = pd.read_csv(csv_path, dtype={"code_postal": str})  # keep leading 0s
    df = df.dropna(
        subset=[
            "code_insee",
            "code_postal",
            "nom_commune",
            "latitude",
            "longitude",
        ]
    )
    df = df[
        ["code_insee", "code_postal", "nom_commune", "latitude", "longitude"]
    ]
    df["normalised_commune"] = df["nom_commune"].apply(normalise_name)
    return df


def load_participant_data(csv_path="code-ville.csv"):
    """Read points to plot."""
    df = pd.read_csv(csv_path, dtype={"code_postal": str})
    df = df.dropna()
    df["normalised_commune"] = df["commune"].apply(normalise_name)
    df = df[["code_postal", "normalised_commune"]]
    return df.values.tolist()


def get_coords_from_postal_and_commune(communes, ref_df):
    """Map postal code and commune to (latitude, longitude)."""
    print("----------")
    print(communes[:5])
    print(ref_df[:5])
    print(ref_df.columns)
    print("----------")
    results = []
    for code_postal, commune in communes:
        # normalised_commune = normalise_name(commune)
        match = ref_df[
            (ref_df["code_postal"] == code_postal)
            & (ref_df["normalised_commune"].str.startswith(commune))
        ]
        if not match.empty:
            row = match.iloc[0]
            results.append((row["latitude"], row["longitude"]))
        else:
            if code_postal != "Sans réponse" or commune != "sans reponse":
                print(f"Failed to find {code_postal}, {commune}")
    return results


def plot_it(coords):
    """Plot a lat/long list over France.

    The default projection (ccrs.PlateCarree(), a simple lat/lon grid)
    can look distorted, especially at higher latitudes like France.

    The Lambert Conformal Conic projection is commonly used for maps
    of France (and is used by IGN, the national mapping agency). It
    preserves shape and angles reasonably well over mid-latitude
    regions.

    """
    # Separate lats and lons
    lats, lons = zip(*coords)

    # Use Lambert Conformal projection centered on France
    projection = ccrs.LambertConformal(
        central_longitude=3, central_latitude=46.5
    )

    # Create a map
    fig = plt.figure(figsize=(10, 12))
    ax = plt.axes(projection=projection)

    # Set extent to cover France
    ax.set_extent(
        [-5, 10, 41, 52], crs=ccrs.PlateCarree()
    )  # [west, east, south, north]

    # Add features
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
    ax.add_feature(cfeature.LAKES, facecolor="lightblue")
    ax.add_feature(cfeature.RIVERS)
    # ax.add_feature(cfeature.STATES)

    # Plot the points
    print(
        f"Plotting {len(coords)} points through a lambert conformal projection."
    )
    print("This might take a moment.")
    ax.scatter(
        lons, lats, color="red", s=10, transform=ccrs.PlateCarree(), zorder=5
    )

    plt.title("Inscriptions en France")
    plt.savefig("carte_codes_postaux.png", dpi=300)
    plt.close()


geo_lookup_df = load_commune_data()
participants = load_participant_data()
coords = get_coords_from_postal_and_commune(participants, geo_lookup_df)
plot_it(coords)
