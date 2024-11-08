import json
from collections import defaultdict
import re


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_field(entry, prefix):
    """
    Extract the value from the entry where the key starts with the given prefix.
    Returns None if not found.
    """
    for key, value in entry.items():
        if key.startswith(prefix):
            return value
    return None


def count_items(items):
    """
    Count occurrences of each item in the list.
    Returns a dictionary with item as key and count as value.
    """
    counts = defaultdict(int)
    for item in items:
        counts[item] += 1
    return counts


def sanitize_anchor(text):
    """
    Sanitize the internal_id to create a valid markdown anchor.
    GitHub automatically converts anchors to lowercase and replaces spaces with hyphens.
    Remove any characters that are not alphanumeric or hyphens.
    """
    text = text.lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    return text


def format_items_markdown_list(items, props_dict):
    """
    Format a list of items as a Markdown unordered list.
    Each item is formatted as:
    - ItemName xN ([internal_id](props.md#anchor))
    If N is 1, omit the xN.
    If the item name is missing, use internal_id as the name.
    """
    counts = count_items(items)
    formatted = []
    for internal_id, count in counts.items():
        prop = props_dict.get(internal_id, {})
        name = prop.get("Name", internal_id)
        anchor = sanitize_anchor(internal_id)
        if name == "N/A":
            name = internal_id
        if count > 1:
            item_str = f"{name} x{count} ([{internal_id}](props.md#{anchor}))"
        else:
            item_str = f"{name} ([{internal_id}](props.md#{anchor}))"
        formatted.append(item_str)
    return "</br>".join(formatted)


def escape_markdown(text):
    """
    Escape markdown special characters in text.
    """
    if not isinstance(text, str):
        return text
    return text.replace("|", "\\|").replace("\n", " ")


def main():
    # Define input and output file paths
    props_file = "props.json"
    craft_recipes_file = "craftRecipes.json"
    props_md = "props.md"
    craft_recipes_md = "craft_recipes.md"

    # Load JSON data
    props_data = load_json(props_file)[0]  # Assuming the JSON array has one object
    craft_data = load_json(craft_recipes_file)[0]

    # Process props
    props_rows = props_data.get("Rows", {})
    props_list = []
    props_dict = {}  # For quick lookup by internal_id

    for internal_id, details in props_rows.items():
        name_entry = extract_field(details, "displayName")
        name = (
            name_entry.get("SourceString") if name_entry else internal_id
        )  # Use internal_id if name missing

        price = details.get(
            next((k for k in details if k.startswith("price_")), "price"), "N/A"
        )

        description_entry = extract_field(details, "description")
        description = (
            description_entry.get("SourceString") if description_entry else "N/A"
        )

        props_list.append(
            {
                "Name": name,
                "Internal Id": internal_id,
                "Price": price,
                "Description": description,
            }
        )

        props_dict[internal_id] = {"Name": name if name != "N/A" else internal_id}

    # Sort props_list by Name if available, else by Internal Id
    props_list.sort(
        key=lambda x: x["Name"].lower() if x["Name"] else x["Internal Id"].lower()
    )

    # Write props.md
    with open(props_md, "w", encoding="utf-8") as f:
        f.write("# Props\n\n")
        f.write("| Internal Id | Name | Price | Description |\n")
        f.write("| --- | --- | --- | --- |\n")
        for prop in props_list:
            anchor = sanitize_anchor(prop["Internal Id"])
            internal_id_link = f"<a id=\"{anchor}\"></a> [{escape_markdown(prop['Internal Id'])}](#{anchor})"
            name = escape_markdown(prop["Name"])
            price = escape_markdown(str(prop["Price"]))
            description = escape_markdown(prop["Description"])
            f.write(f"| {internal_id_link} | {name} | {price} | {description} |\n")

    print(f"Generated {props_md}")

    # Process craftRecipes
    craft_rows = craft_data.get("Rows", {})
    craft_list = []

    for recipe_id, details in craft_rows.items():
        # Extract results
        result_entry = extract_field(details, "result")
        results = result_entry if result_entry else []

        # Extract ingredients
        ingredients_entry = extract_field(details, "ingredients")
        ingredients = ingredients_entry if ingredients_entry else []

        # Extract blueprint
        blueprint = details.get(
            next((k for k in details if k.startswith("blueprint_")), "blueprint"), ""
        )
        blueprint = blueprint if blueprint else "N/A"

        # Extract reverse
        reverse = details.get(
            next((k for k in details if k.startswith("reverse_")), "reverse"), False
        )
        reverse_icon = "✅" if reverse else "❌"

        # Format results and ingredients as Markdown lists
        formatted_results = format_items_markdown_list(results, props_dict)
        formatted_ingredients = format_items_markdown_list(ingredients, props_dict)

        craft_list.append(
            {
                "Result": formatted_results,
                "Recipe": formatted_ingredients,
                "Blueprint": blueprint,
                "Reversible": reverse_icon,
            }
        )

    # Sort craft_list by Result (using first item name for sorting)
    def sort_key(craft):
        first_line = craft["Result"].split("\n")[0]
        match = re.match(r"-\s+(.*?)\s+\(", first_line)
        return match.group(1).lower() if match else ""

    craft_list.sort(key=sort_key)

    # Write craft_recipes.md
    with open(craft_recipes_md, "w", encoding="utf-8") as f:
        f.write("# Craft Recipes\n\n")
        f.write("| Result | Recipe | Blueprint | Reversible |\n")
        f.write("| --- | --- | --- | --- |\n")
        for craft in craft_list:
            result = escape_markdown(craft["Result"])
            recipe = escape_markdown(craft["Recipe"])
            blueprint = escape_markdown(craft["Blueprint"])
            reversible = craft["Reversible"]
            f.write(f"| {result} | {recipe} | {blueprint} | {reversible} |\n")

    print(f"Generated {craft_recipes_md}")


if __name__ == "__main__":
    main()
