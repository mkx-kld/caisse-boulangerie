# Fichier: utils.py (Version finale avec traduction)

from translations import get_text

def format_currency(value):
    """
    Formate une valeur numérique en une chaîne de caractères monétaire,
    en utilisant le symbole de la devise du fichier de traduction.
    """
    try:
        numeric_value = int(round(float(value)))
        formatted_number = f"{numeric_value:,}".replace(",", " ")
        
        # MODIFIÉ : On récupère le symbole de la monnaie depuis les traductions
        symbol = get_text("currency_symbol")
        
        # On revient à l'affichage que vous préférez (symbole à droite)
        return f"{formatted_number} {symbol}"
        
    except (ValueError, TypeError):
        # On utilise aussi le symbole traduit pour la valeur par défaut
        return f"0 {get_text('currency_symbol')}"