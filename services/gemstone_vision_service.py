"""
Gemstone identification service using Gemini Vision API + RAG
Analyzes gemstone images and provides detailed identification with expert knowledge
DOMAIN RESTRICTED: Only identifies gemstones and minerals, rejects non-gemstone images
"""

import json
import logging
from typing import Dict, Any, List
from google import genai
from google.genai import types
from PIL import Image

from config.settings import GEMINI_API_KEY
from rag_systems.vector_rag_system import semantic_search

# Configure logging
logger = logging.getLogger(__name__)


class GemstoneVisionService:
    """Service for identifying gemstones using Gemini Vision API"""

    def __init__(self):
        """Initialize Gemini Vision API"""
        # Configure Gemini API with new package
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        logger.info(
            "GemstoneVisionService initialized with Gemini 2.5 Flash (Domain Restricted)"
        )

    def identify_gemstone(self, image: Image.Image) -> Dict[str, Any]:
        """
        Identify gemstone from image using Gemini Vision

        DOMAIN RESTRICTION: Only identifies gemstones, minerals, and precious stones.
        Rejects non-gemstone images (animals, people, objects, etc.)

        Args:
            image: PIL Image object of the gemstone

        Returns:
            Dictionary containing identification results or rejection message
        """
        try:
            # Domain-restricted prompt for gemstone identification ONLY
            prompt = """You are an expert gemologist specializing in gemstone identification. 

**CRITICAL DOMAIN RESTRICTION:**
You ONLY identify GEMSTONES, MINERALS, and PRECIOUS STONES.
If the image shows anything other than a gemstone (person, animal, plant, object, food, etc.), you MUST respond with:
{
    "gemstone_name": "NOT_A_GEMSTONE",
    "confidence": "High",
    "description": "This image does not contain a gemstone. I am specialized in gemstone identification only. Please provide an image of a gemstone, mineral, or precious stone.",
    "is_gemstone": false
}

**ACCEPTED ITEMS FOR IDENTIFICATION:**
✅ Gemstones (cut or rough)
✅ Minerals and crystals
✅ Precious stones (Ruby, Sapphire, Emerald, Diamond)
✅ Semi-precious stones (Agate, Quartz, Jade, Turquoise, etc.)
✅ Organic gems (Pearl, Amber, Coral)

❌ REJECTED ITEMS (respond with NOT_A_GEMSTONE):
❌ People, animals, plants
❌ Jewelry settings (without visible stone)
❌ Regular objects, food, buildings
❌ Photographs, paintings, screens
❌ Anything not a gemstone/mineral

**GEMSTONE TYPES TO IDENTIFY:**

AGATES (Most Common in Our Region):
- Carnelian: Orange-red to deep red agate
- Onyx: Black and white banded agate
- Sardonyx: Brown and white banded
- Moss Agate: Clear/white with green moss-like inclusions
- Dendritic Agate: Tree-like fern patterns
- Banded Agate: Concentric colored bands
- Eye Agate: Circular eye patterns
- Fortification Agate: Angular geometric banding
- Fire Agate: Iridescent rainbow colors
- Blue Lace Agate: Light blue with white lacy bands
- Yemeni Agate: Regional varieties (red, yellow, black, white, banded)
- Buqran Agate: Multi-layer banded (red/white/black)

OTHER COMMON GEMSTONES:
- Quartz: Amethyst (purple), Citrine (yellow), Rose Quartz (pink), Smoky Quartz (brown)
- Jasper: Opaque, red/brown with patterns
- Turquoise/Firooza: Blue-green opaque
- Jade: Green, translucent to opaque
- Lapis Lazuli: Deep blue with gold pyrite
- Malachite: Green with banding
- Tiger's Eye: Brown with chatoyancy
- Moonstone: White/peach with adularescence

**IDENTIFICATION STEPS:**
1. FIRST: Confirm this IS a gemstone/mineral. If not → return NOT_A_GEMSTONE
2. Identify SPECIFIC TYPE (e.g., "Carnelian Agate" NOT just "Agate")
3. Look for: banding, patterns, inclusions, color, transparency, luster
4. Note ANY banding/patterns = likely AGATE variety
5. Rate confidence: High (90%+), Medium (60-90%), Low (<60%)
6. Describe 4Cs (Color, Cut, Clarity, Carat estimate)
7. Care instructions
8. Search keywords

**RESPONSE FORMAT (JSON ONLY - NO MARKDOWN):**
{
    "gemstone_name": "Carnelian Agate",
    "scientific_name": "Chalcedony (SiO2 - microcrystalline quartz)",
    "confidence": "High",
    "is_gemstone": true,
    "properties": {
        "color": "Translucent orange-red with darker banding",
        "cut": "Oval cabochon cut",
        "clarity": "Translucent with minor natural inclusions",
        "carat_estimate": "Approximately 3-5 carats"
    },
    "description": "Natural carnelian agate, a variety of chalcedony with characteristic orange-red color from iron oxide. Shows typical banding and translucency. Color often enhanced by heat treatment.",
    "care_instructions": "Clean with mild soap and water. Avoid harsh chemicals and extreme temperature changes. Hardness 7 on Mohs scale - durable for jewelry. Store separately to prevent scratching.",
    "search_keywords": ["carnelian", "red agate", "agate", "chalcedony", "yemeni carnelian"]
}

**CRITICAL RULES:**
- Return ONLY valid JSON (no markdown, no code blocks, no extra text)
- If NOT a gemstone → gemstone_name: "NOT_A_GEMSTONE", is_gemstone: false
- Always include "is_gemstone": true or false
- Be SPECIFIC with gemstone types (not generic)
- If uncertain but IS a gemstone, provide best identification with Lower confidence"""

            # Generate content with image
            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash", contents=[prompt, image]
            )

            # Extract and parse response
            raw_response = response.text.strip()
            logger.info(f"Gemini raw response: {raw_response[:200]}...")

            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                clean_response = raw_response
                if "```json" in clean_response:
                    clean_response = (
                        clean_response.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in clean_response:
                    clean_response = (
                        clean_response.split("```")[1].split("```")[0].strip()
                    )

                result = json.loads(clean_response)

                # Check if image was rejected as non-gemstone
                if (
                    result.get("gemstone_name") == "NOT_A_GEMSTONE"
                    or result.get("is_gemstone") == False
                ):
                    logger.warning("Image rejected: Not a gemstone")
                    return {
                        "success": False,
                        "gemstone_name": "NOT_A_GEMSTONE",
                        "confidence": "High",
                        "description": result.get(
                            "description",
                            "This is not a gemstone. Please provide an image of a gemstone, mineral, or precious stone for identification.",
                        ),
                        "is_gemstone": False,
                        "error": "domain_restriction",
                        "message": "I am specialized in gemstone identification only. Please scan a gemstone.",
                        "search_keywords": [],
                    }

                # Valid gemstone identification
                result["success"] = True
                result["raw_response"] = raw_response
                result["is_gemstone"] = True

                # Ensure search_keywords exists
                if "search_keywords" not in result:
                    result["search_keywords"] = [
                        result.get("gemstone_name", "").lower(),
                        "gemstone",
                        "natural stone",
                    ]

                logger.info(
                    f"Successfully identified: {result.get('gemstone_name')} "
                    f"(Confidence: {result.get('confidence')})"
                )

                # Enhance with RAG knowledge
                result = self._enhance_with_rag(result)

                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON: {e}")
                logger.error(f"Raw response: {raw_response}")

                return {
                    "success": False,
                    "error": "parse_error",
                    "gemstone_name": "Unknown",
                    "confidence": "Low",
                    "description": "Could not parse identification results. Please try with a clearer gemstone image.",
                    "raw_response": raw_response,
                    "search_keywords": [],
                }

        except Exception as e:
            logger.error(f"Gemstone identification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "gemstone_name": "Unknown",
                "confidence": "Low",
                "description": f"Identification failed: {str(e)}",
                "search_keywords": [],
            }

    def _enhance_with_rag(
        self, identification_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance identification with expert knowledge from RAG system

        Args:
            identification_result: Result from Gemini Vision identification

        Returns:
            Enhanced result with expert knowledge added
        """
        try:
            gemstone_name = identification_result.get("gemstone_name", "gemstone")

            # Skip RAG if not a successful gemstone identification
            if not identification_result.get("success") or gemstone_name == "Unknown":
                logger.info("Skipping RAG enhancement - no valid identification")
                return identification_result

            # Build RAG query
            rag_query = (
                f"{gemstone_name} properties characteristics grading identification"
            )
            logger.info(f"Querying RAG system: {rag_query}")

            # Query RAG system (used internally for context, not shown to user)
            rag_results = semantic_search(rag_query, top_k=3)

            if rag_results:
                # RAG results exist and can enhance the model's understanding
                # But we don't include the raw chunks in the response (too technical/messy)
                sources = []
                for doc in rag_results:
                    score = doc.get("similarity_score", 0)
                    if score > 0.5:
                        source = doc.get("metadata", {}).get("source", "Knowledge Base")
                        if source not in sources:
                            sources.append(source)

                # Only add source references, not the raw content
                if sources:
                    identification_result["knowledge_sources"] = sources
                    identification_result["rag_enhanced"] = True
                    logger.info(
                        f"RAG enhancement: Found {len(sources)} relevant sources"
                    )
                else:
                    identification_result["rag_enhanced"] = False
                    logger.info("RAG results below relevance threshold")
            else:
                identification_result["rag_enhanced"] = False
                logger.info("No RAG results found")

            return identification_result

        except Exception as e:
            logger.error(f"RAG enhancement failed: {e}")
            identification_result["rag_enhanced"] = False
            identification_result["rag_error"] = str(e)
            return identification_result

    def get_matching_products(
        self, search_keywords: List[str], db_connection, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find products matching identified gemstone"""
        try:
            cursor = db_connection.cursor()

            placeholders = " OR ".join(
                [
                    "(p.name ILIKE %s OR p.description ILIKE %s OR p.stone_type ILIKE %s)"
                    for _ in search_keywords
                ]
            )

            query = f"""
                SELECT 
                    p.id, p.name, p.description, p.stone_type,
                    p.carat_weight, p.color, p.clarity, p.cut_type,
                    p.price, p.stock_quantity, p.image_url,
                    COALESCE(AVG(r.rating), 0) as avg_rating
                FROM products p
                LEFT JOIN reviews r ON p.id = r.product_id
                WHERE {placeholders}
                AND p.stock_quantity > 0
                GROUP BY p.id
                ORDER BY avg_rating DESC, p.price ASC
                LIMIT %s
            """

            params = []
            for keyword in search_keywords:
                search_term = f"%{keyword}%"
                params.extend([search_term, search_term, search_term])
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            products = []
            for row in rows:
                products.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "stone_type": row[3],
                        "carat_weight": float(row[4]) if row[4] else None,
                        "color": row[5],
                        "clarity": row[6],
                        "cut_type": row[7],
                        "price": float(row[8]) if row[8] else 0,
                        "stock_quantity": row[9],
                        "image_url": row[10],
                        "avg_rating": float(row[11]) if row[11] else 0,
                    }
                )

            cursor.close()
            logger.info(f"Found {len(products)} matching products")
            return products

        except Exception as e:
            logger.error(f"Failed to fetch matching products: {e}")
            return []
