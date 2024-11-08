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


def format_item(name, internal_id):
    """
    Format the item name with a markdown link to its anchor.
    If name is None, use the internal_id as the display name without a link.
    """
    if name:
        # Sanitize the internal_id to create a valid anchor
        anchor = sanitize_anchor(internal_id)
        return f"[{name}](#{anchor})"
    else:
        return internal_id


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


def format_items(items, props_dict):
    """
    Format a list of items with their names and links.
    If multiple of the same item are present, append 'xN' where N is the count.
    If an item's name is not found in props_dict, use the internal_id.
    Returns a comma-separated string of formatted items.
    """
    counts = count_items(items)
    formatted = []
    for internal_id, count in counts.items():
        name = props_dict.get(internal_id, {}).get("Name")
        formatted_name = format_item(name, internal_id)
        if count > 1:
            formatted_name += f" x{count}"
        formatted.append(formatted_name)
    return ", ".join(formatted)


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
        name = name_entry.get("SourceString") if name_entry else "N/A"

        price = details.get(
            next((k for k in details if k.startswith("price_")), "price"), "N/A"
        )

        description_entry = extract_field(details, "description")
        description = (
            description_entry.get("SourceString") if description_entry else "N/A"
        )

        props_list.append(
            {
                "Name": name if name else internal_id,
                "Internal Id": internal_id,
                "Price": price,
                "Description": description,
            }
        )

        props_dict[internal_id] = {"Name": name}

    # Sort props_list by Name
    props_list.sort(key=lambda x: x["Name"].lower())

    # Write props.md
    with open(props_md, "w", encoding="utf-8") as f:
        f.write("| Name | Internal Id | Price | Description |\n")
        f.write("| --- | --- | --- | --- |\n")
        for prop in props_list:
            anchor = sanitize_anchor(prop["Internal Id"])
            name_link = (
                f"<a id=\"{anchor}\"></a> [{escape_markdown(prop['Name'])}](#{anchor})"
            )
            internal_id = escape_markdown(prop["Internal Id"])
            price = escape_markdown(str(prop["Price"]))
            description = escape_markdown(prop["Description"])
            f.write(f"| {name_link} | {internal_id} | {price} | {description} |\n")

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

        # Extract reverse
        reverse = details.get(
            next((k for k in details if k.startswith("reverse_")), "reverse"), False
        )
        reverse_icon = "✅" if reverse else "❌"

        # Format results and ingredients
        formatted_results = format_items(results, props_dict)
        formatted_ingredients = format_items(ingredients, props_dict)

        craft_list.append(
            {
                "Result": formatted_results,
                "Recipe": formatted_ingredients,
                "Blueprint": blueprint if blueprint else "N/A",
                "Reversible": reverse_icon,
            }
        )

    # Sort craft_list by Result
    craft_list.sort(key=lambda x: x["Result"].lower())

    # Write craft_recipes.md
    with open(craft_recipes_md, "w", encoding="utf-8") as f:
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
