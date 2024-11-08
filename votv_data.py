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
    Sanitize the text to create a valid markdown anchor.
    GitHub automatically converts anchors to lowercase and replaces spaces with hyphens.
    Remove any characters that are not alphanumeric or hyphens.
    """
    text = text.lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    return text


def format_prop_link(name, internal_id):
    """
    Format the prop name with a markdown link to its anchor in props.md.
    """
    anchor = sanitize_anchor(internal_id)
    if name:
        return f"{name} ([{internal_id}](props.md#{anchor}))"
    else:
        return f"[{internal_id}](props.md#{anchor})"


def format_tag_link(tag):
    """
    Format the tag with a markdown link to its anchor in props_by_tags.md.
    """
    anchor = sanitize_anchor(tag)
    return f"[{tag}](props_by_tags.md#{anchor})"


def format_item(name, internal_id, props_dict, link_to_props=True):
    """
    Format the item name with a markdown link.
    If link_to_props is True, link points to props.md#anchor.
    If name is None, use the internal_id as the display name without a link.
    """
    if name:
        anchor = sanitize_anchor(internal_id)
        if link_to_props:
            return f"{name} ([{internal_id}](props.md#{anchor}))"
        else:
            return name
    else:
        if link_to_props:
            anchor = sanitize_anchor(internal_id)
            return f"[{internal_id}](props.md#{anchor})"
        else:
            return internal_id


def format_items_list(items, props_dict):
    """
    Format a list of items with their names and links as a markdown list.
    If multiple of the same item are present, append 'xN' where N is the count.
    Returns a markdown list string separated by <br>.
    """
    counts = count_items(items)
    formatted = []
    for internal_id, count in counts.items():
        name = props_dict.get(internal_id, {}).get("Name", internal_id)
        if count > 1:
            name_with_count = f"{name} x{count}"
        else:
            name_with_count = name
        # Format as '- Name xN ([internal_id](props.md#anchor))' or '- internal_id'
        item_str = format_item(
            name_with_count, internal_id, props_dict, link_to_props=True
        )
        formatted.append(f"- {item_str}")
    return "<br>".join(formatted)


def format_tags_list(tags, link_to_tags=True):
    """
    Format a list of tags with their links as a markdown list.
    If multiple of the same tag are present, append 'xN' where N is the count.
    Returns a markdown list string separated by <br>.
    """
    counts = count_items(tags)
    formatted = []
    for tag, count in counts.items():
        tag_str = f"Items tagged {tag}"
        if count > 1:
            tag_str += f" x{count}"
        if link_to_tags:
            tag_str = f"{tag_str} ([{tag}](props_by_tags.md#{sanitize_anchor(tag)}))"
        formatted.append(f"- {tag_str}")
    return "<br>".join(formatted)


def escape_markdown(text):
    """
    Escape markdown special characters in text.
    """
    if not isinstance(text, str):
        return text
    return text.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def main():
    # Define input and output file paths
    props_file = "props.json"
    craft_recipes_file = "craftRecipes.json"
    props_md = "props.md"
    craft_recipes_md = "craft_recipes.md"
    props_by_tags_md = "props_by_tags.md"

    # Load JSON data
    props_data = load_json(props_file)[0]  # Assuming the JSON array has one object
    craft_data = load_json(craft_recipes_file)[0]

    # Process props
    props_rows = props_data.get("Rows", {})
    props_list = []
    props_dict = {}  # For quick lookup by internal_id
    tag_to_items = defaultdict(list)  # tag -> list of internal_ids

    for internal_id, details in props_rows.items():
        # Extract displayName
        name_entry = extract_field(details, "displayName")
        name = (
            name_entry.get("SourceString")
            if name_entry and "SourceString" in name_entry
            else internal_id
        )

        # Extract price
        price_key = next((k for k in details if k.startswith("price_")), None)
        price = details.get(price_key, "N/A")

        # Extract description
        description_entry = extract_field(details, "description")
        description = (
            description_entry.get("SourceString")
            if description_entry and "SourceString" in description_entry
            else "N/A"
        )

        # Extract craftTags
        # craft_tag_keys = [k for k in details if k.startswith("craftTag_")]
        tags = [
            v
            for k, v in details.items()
            if k.startswith("craftTag_") and isinstance(v, str) and v
        ]
        for tag in tags:
            tag_to_items[tag].append(internal_id)

        props_list.append(
            {
                "Name": name,
                "Internal Id": internal_id,
                "Price": price,
                "Description": description,
            }
        )

        props_dict[internal_id] = {"Name": name}

    # Sort props_list by Name (case-insensitive), using Internal Id if Name is missing
    props_list.sort(key=lambda x: (x["Name"] or x["Internal Id"]).lower())

    # Write props.md
    with open(props_md, "w", encoding="utf-8") as f:
        f.write("| Name | Internal Id | Price | Description |\n")
        f.write("| --- | --- | --- | --- |\n")
        for prop in props_list:
            # The anchor is on Internal Id column
            anchor = sanitize_anchor(prop["Internal Id"])
            name = escape_markdown(prop["Name"])
            # Internal Id with anchor and link to itself in props.md
            internal_id = escape_markdown(prop["Internal Id"])
            internal_id_link = f'[{internal_id}](#{anchor})<a id="{anchor}"></a>'
            price = escape_markdown(str(prop["Price"]))
            description = escape_markdown(prop["Description"])
            f.write(f"| {name} | {internal_id_link} | {price} | {description} |\n")

    print(f"Generated {props_md}")

    # Create props_by_tags.md
    with open(props_by_tags_md, "w", encoding="utf-8") as f:
        f.write("# Props by Tags\n\n")
        if not tag_to_items:
            f.write("No tags found in props.\n")
        else:
            for tag in sorted(tag_to_items.keys(), key=lambda x: x.lower()):
                anchor = sanitize_anchor(tag)
                f.write(f'## {tag}\n<a id="{anchor}"></a>\n\n')
                f.write("| Name | Internal Id | Price | Description |\n")
                f.write("| --- | --- | --- | --- |\n")
                for internal_id in tag_to_items[tag]:
                    prop = next(
                        (p for p in props_list if p["Internal Id"] == internal_id), None
                    )
                    if prop:
                        name = escape_markdown(prop["Name"])
                        anchor_prop = sanitize_anchor(prop["Internal Id"])
                        internal_id_escaped = escape_markdown(prop["Internal Id"])
                        internal_id_link = (
                            f"[{internal_id_escaped}](props.md#{anchor_prop})"
                        )
                        price = escape_markdown(str(prop["Price"]))
                        description = escape_markdown(prop["Description"])
                        f.write(
                            f"| {name} | {internal_id_link} | {price} | {description} |\n"
                        )
                f.write("\n")

    print(f"Generated {props_by_tags_md}")

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

        # Extract craftTags
        craft_tags_entry = extract_field(details, "craftTags")
        craft_tags = craft_tags_entry if craft_tags_entry else []

        # Extract blueprint
        blueprint_key = next((k for k in details if k.startswith("blueprint_")), None)
        blueprint = details.get(blueprint_key, "") if blueprint_key else ""

        # Extract reverse
        reverse_key = next((k for k in details if k.startswith("reverse_")), None)
        reverse = details.get(reverse_key, False) if reverse_key else False
        reverse_icon = "✅" if reverse else "❌"

        # Format results and ingredients as markdown lists
        formatted_results = format_items_list(results, props_dict) if results else "N/A"
        formatted_ingredients = (
            format_items_list(ingredients, props_dict) if ingredients else ""
        )

        # Format craftTags as markdown lists
        formatted_craft_tags = (
            format_tags_list(craft_tags, link_to_tags=True) if craft_tags else ""
        )

        # Combine ingredients and craftTags
        if formatted_ingredients and formatted_craft_tags:
            combined_recipe = f"{formatted_ingredients}<br>{formatted_craft_tags}"
        elif formatted_ingredients:
            combined_recipe = formatted_ingredients
        elif formatted_craft_tags:
            combined_recipe = formatted_craft_tags
        else:
            combined_recipe = "N/A"

        # Handle blueprint
        blueprint_display = blueprint if blueprint else "N/A"

        craft_list.append(
            {
                "Result": formatted_results,
                "Recipe": combined_recipe,
                "Blueprint": escape_markdown(blueprint_display),
                "Reversible": reverse_icon,
            }
        )

    # Sort craft_list by Result (case-insensitive)
    craft_list.sort(
        key=lambda x: x["Result"].lower() if isinstance(x["Result"], str) else ""
    )

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
