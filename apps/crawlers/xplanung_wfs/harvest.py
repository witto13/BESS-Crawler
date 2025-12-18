"""
XPlanung WFS harvester for structured planning data.
"""
from typing import List, Dict, Optional
import requests
from xml.etree import ElementTree as ET
from urllib.parse import urlencode, urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "ows": "http://www.opengis.net/ows/1.1",
    "xplan": "http://www.xplanung.de/xplangml/6/0",
}


def get_layers(capabilities_url: str) -> List[str]:
    """
    Parse WFS GetCapabilities and return layer names.
    """
    layers = []
    try:
        params = {"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}
        resp = requests.get(capabilities_url, params=params, timeout=30)
        if resp.status_code != 200:
            return layers
        
        root = ET.fromstring(resp.content)
        
        # Find FeatureTypeList
        for feature_type in root.findall(".//{http://www.opengis.net/wfs/2.0}FeatureType"):
            name_elem = feature_type.find("{http://www.opengis.net/ows/1.1}Name")
            if name_elem is not None:
                layers.append(name_elem.text)
    except Exception as e:
        logger.warning("Failed to get layers from %s: %s", capabilities_url, e)
    
    return layers


def harvest_layer(layer_url: str, layer_name: str, max_features: int = 1000) -> List[Dict]:
    """
    Harvest features from a WFS layer (B-Plan, FNP, etc.).
    """
    features = []
    
    try:
        # WFS GetFeature request
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typenames": layer_name,
            "outputFormat": "application/json",  # Prefer GeoJSON
            "count": min(max_features, 100),  # Start with smaller batches
        }
        
        start_index = 0
        while len(features) < max_features:
            params["startIndex"] = start_index
            
            resp = requests.get(layer_url, params=params, timeout=30)
            if resp.status_code != 200:
                break
            
            # Try to parse as GeoJSON
            try:
                data = resp.json()
                if "features" in data:
                    batch = data["features"]
                    if not batch:
                        break
                    features.extend(batch)
                    start_index += len(batch)
                else:
                    break
            except:
                # Fallback: try XML
                root = ET.fromstring(resp.content)
                for member in root.findall(".//{http://www.opengis.net/wfs/2.0}member"):
                    # Extract attributes
                    feature = {}
                    for child in member.iter():
                        if child.tag and "}" in child.tag:
                            tag_name = child.tag.split("}")[-1]
                            feature[tag_name] = child.text
                    if feature:
                        features.append(feature)
                break  # XML parsing is simpler, don't paginate
        
        # Normalize features
        normalized = []
        for feat in features[:max_features]:
            # Extract common XPlanung attributes
            normalized.append({
                "name": feat.get("name") or feat.get("bezeichnung") or "",
                "planart": feat.get("planart") or feat.get("planArt") or "",
                "gemeinde": feat.get("gemeinde") or feat.get("gemeindename") or "",
                "status": feat.get("status") or "",
                "geometry": feat.get("geometry") if isinstance(feat.get("geometry"), dict) else None,
                "raw": feat,
            })
    except Exception as e:
        logger.warning("Failed to harvest layer %s: %s", layer_name, e)
    
    return normalized

