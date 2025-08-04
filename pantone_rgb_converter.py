import requests
import json
from typing import Dict, Tuple, Optional
import sys

# Try to import optional libraries for color display
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from colorama import init, Fore, Back, Style
    init()  # Initialize colorama
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

class PantoneRGBConverter:
    def __init__(self):
        # Common Pantone to RGB mappings (approximate values)
        # These are approximate conversions - actual values may vary
        self.pantone_rgb_map = {
            # Blues
            "2736": (0, 56, 147),    # Pantone 2736 C
            "2727": (0, 123, 191),   # Pantone 2727 C
            
            # Teals/Cyans
            "3125": (0, 160, 176),   # Pantone 3125 C
            "3275": (0, 166, 156),   # Pantone 3275 C
            
            # Greens
            "368": (105, 190, 40),   # Pantone 368 C
            "396": (181, 189, 0),    # Pantone 396 C
            
            # Yellows/Oranges
            "1235": (255, 184, 28),  # Pantone 1235 C
            "185": (237, 41, 57),    # Pantone 185 C
            
            # Reds/Burgundy
            "202": (146, 39, 36),    # Pantone 202 C
            
            # Greys (approximate Cool Grey and Warm Grey)
            "COOL GREY 7": (153, 153, 153),
            "COOL GREY 10": (99, 102, 106),
            "WARM GREY 6": (169, 160, 149),
            "WARM GREY 8": (147, 135, 123),
            
            # Basic colors
            "BLACK": (0, 0, 0),
            "WHITE": (255, 255, 255),
            "PURPLE": (102, 45, 145),
            "RHODAMINE RED": (233, 30, 132),
            "ORANGE 021": (255, 88, 0),
            "YELLOW": (255, 242, 0),
        }
    
    def get_rgb_from_pantone(self, pantone_code: str) -> Optional[Tuple[int, int, int]]:
        """Get RGB values for a given Pantone code from the local mapping."""
        pantone_code = pantone_code.upper().strip()
        return self.pantone_rgb_map.get(pantone_code)
    
    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color code."""
        return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
    
    def rgb_to_ansi_background(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to ANSI background color code for terminal display."""
        return f"\033[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
    
    def get_text_color_for_background(self, rgb: Tuple[int, int, int]) -> str:
        """Determine if white or black text is better for a given background color."""
        # Calculate luminance
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return "\033[97m" if luminance < 0.5 else "\033[30m"  # White text for dark bg, black for light
    
    def print_color_swatch_terminal(self, color_name: str, rgb: Tuple[int, int, int], hex_val: str):
        """Print a color swatch in the terminal using ANSI codes."""
        if sys.stdout.isatty():  # Check if output is to terminal
            bg_color = self.rgb_to_ansi_background(rgb)
            text_color = self.get_text_color_for_background(rgb)
            reset = "\033[0m"
            
            # Create color swatch
            swatch = f"{bg_color}{text_color}  ████  {reset}"
            print(f"{swatch} {color_name:<20} RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})  {hex_val}")
        else:
            # Fallback for non-terminal output
            print(f"■ {color_name:<20} RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})  {hex_val}")
    
    def print_color_swatch_colorama(self, color_name: str, rgb: Tuple[int, int, int], hex_val: str):
        """Print a color swatch using colorama (limited color support)."""
        # Colorama has limited colors, so we'll approximate
        color_map = {
            (0, 0, 0): Back.BLACK,
            (255, 255, 255): Back.WHITE,
            (255, 0, 0): Back.RED,
            (0, 255, 0): Back.GREEN,
            (0, 0, 255): Back.BLUE,
            (255, 255, 0): Back.YELLOW,
            (255, 0, 255): Back.MAGENTA,
            (0, 255, 255): Back.CYAN,
        }
        
        # Find closest color
        min_distance = float('inf')
        closest_color = Back.WHITE
        
        for color_rgb, back_color in color_map.items():
            distance = sum((a - b) ** 2 for a, b in zip(rgb, color_rgb))
            if distance < min_distance:
                min_distance = distance
                closest_color = back_color
        
        swatch = f"{closest_color}  ████  {Style.RESET_ALL}"
        print(f"{swatch} {color_name:<20} RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})  {hex_val}")
    
    def get_university_palette(self) -> Dict[str, Dict[str, any]]:
        """Get the complete university color palette with RGB and hex values."""
        palette = {
            "primary_palette": {},
            "secondary_palette": {}
        }
        
        # Primary palette (Neutral colors + Pantone 202)
        primary_colors = ["COOL GREY 7", "COOL GREY 10", "WARM GREY 6", "WARM GREY 8", "BLACK", "WHITE", "202"]
        
        for color in primary_colors:
            rgb = self.get_rgb_from_pantone(color)
            if rgb:
                color_name = f"Pantone {color}" if color.isdigit() else color
                palette["primary_palette"][color_name] = {
                    "rgb": rgb,
                    "hex": self.rgb_to_hex(rgb)
                }
        
        # Secondary palette (All other colors)
        all_colors = set(self.pantone_rgb_map.keys())
        secondary_colors = list(all_colors - set(primary_colors))
        
        for color in secondary_colors:
            rgb = self.get_rgb_from_pantone(color)
            if rgb:
                color_name = f"Pantone {color}" if color.isdigit() else color
                palette["secondary_palette"][color_name] = {
                    "rgb": rgb,
                    "hex": self.rgb_to_hex(rgb)
                }
        
        return palette
    
    def print_palette(self):
        """Print the complete color palette with color swatches."""
        palette = self.get_university_palette()
        
        print("UNIVERSITY COLOR PALETTE")
        print("=" * 60)
        
        # Show which display method is being used
        if sys.stdout.isatty():
            print("🎨 Color swatches displayed using ANSI terminal colors")
        elif COLORAMA_AVAILABLE:
            print("🎨 Color swatches displayed using colorama (approximate colors)")
        else:
            print("🎨 Color swatches displayed using text symbols")
        print()
        
        for category, colors in palette.items():
            print(f"{category.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for color_name, values in colors.items():
                rgb = values["rgb"]
                hex_val = values["hex"]
                
                # Choose display method based on available libraries
                if sys.stdout.isatty():
                    self.print_color_swatch_terminal(color_name, rgb, hex_val)
                elif COLORAMA_AVAILABLE:
                    self.print_color_swatch_colorama(color_name, rgb, hex_val)
                else:
                    # Fallback: just use a square symbol
                    print(f"■ {color_name:<20} RGB({rgb[0]:3}, {rgb[1]:3}, {rgb[2]:3})  {hex_val}")
            print()
    
    def create_color_palette_image(self, output_filename: str = "university_palette.png"):
        """Create a visual palette image using PIL."""
        if not PIL_AVAILABLE:
            print("PIL (Pillow) not available. Install with: pip install Pillow")
            return
        
        palette = self.get_university_palette()
        
        # Calculate image dimensions
        colors_per_row = 6
        swatch_size = 80
        margin = 10
        text_height = 60
        
        total_colors = sum(len(colors) for colors in palette.values())
        rows = (total_colors + colors_per_row - 1) // colors_per_row
        
        img_width = colors_per_row * (swatch_size + margin) + margin
        img_height = rows * (swatch_size + text_height + margin) + margin + 100  # Extra space for title
        
        # Create image
        img = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("arial.ttf", 12)
            title_font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # Draw title
        draw.text((margin, margin), "University Color Palette", fill='black', font=title_font)
        
        # Draw color swatches
        x, y = margin, margin + 50
        
        for category, colors in palette.items():
            # Category title
            draw.text((x, y), category.replace('_', ' ').title(), fill='black', font=font)
            y += 20
            
            for color_name, values in colors.items():
                rgb = values["rgb"]
                hex_val = values["hex"]
                
                # Draw color swatch
                draw.rectangle([x, y, x + swatch_size, y + swatch_size], fill=rgb)
                draw.rectangle([x, y, x + swatch_size, y + swatch_size], outline='black', width=1)
                
                # Draw color info
                draw.text((x, y + swatch_size + 5), color_name[:15], fill='black', font=font)
                draw.text((x, y + swatch_size + 20), f"RGB{rgb}", fill='black', font=font)
                draw.text((x, y + swatch_size + 35), hex_val, fill='black', font=font)
                
                # Move to next position
                x += swatch_size + margin
                if x + swatch_size > img_width - margin:
                    x = margin
                    y += swatch_size + text_height + margin
        
        img.save(output_filename)
        print(f"Color palette image saved as: {output_filename}")
    
    def create_matplotlib_palette(self):
        """Create a color palette visualization using matplotlib."""
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib not available. Install with: pip install matplotlib")
            return
        
        palette = self.get_university_palette()
        
        fig, axes = plt.subplots(len(palette), 1, figsize=(12, 8))
        if len(palette) == 1:
            axes = [axes]
        
        fig.suptitle('University Color Palette', fontsize=16, fontweight='bold')
        
        for idx, (category, colors) in enumerate(palette.items()):
            ax = axes[idx]
            ax.set_title(category.replace('_', ' ').title(), fontweight='bold')
            
            color_count = len(colors)
            bar_height = 0.8
            
            for i, (color_name, values) in enumerate(colors.items()):
                rgb = values["rgb"]
                hex_val = values["hex"]
                rgb_normalized = tuple(c/255.0 for c in rgb)
                
                # Create color rectangle
                rect = patches.Rectangle((i, 0), 1, bar_height, 
                                       facecolor=rgb_normalized, 
                                       edgecolor='black', 
                                       linewidth=0.5)
                ax.add_patch(rect)
                
                # Add text labels
                text_color = 'white' if sum(rgb) < 384 else 'black'  # Choose contrasting text
                ax.text(i + 0.5, bar_height/2, f'{color_name}\nRGB{rgb}\n{hex_val}', 
                       ha='center', va='center', fontsize=8, color=text_color, fontweight='bold')
            
            ax.set_xlim(0, color_count)
            ax.set_ylim(0, bar_height)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_aspect('equal')
        
        plt.tight_layout()
        plt.savefig('university_palette_matplotlib.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("Matplotlib palette saved as: university_palette_matplotlib.png")
    
    def get_css_variables(self) -> str:
        """Generate CSS custom properties for the color palette."""
        palette = self.get_university_palette()
        css_vars = [":root {"]
        
        for category, colors in palette.items():
            css_vars.append(f"  /* {category.replace('_', ' ').title()} */")
            
            for color_name, values in colors.items():
                # Create CSS-friendly variable name
                var_name = color_name.lower().replace(" ", "-").replace("pantone-", "")
                css_vars.append(f"  --{var_name}: {values['hex']};")
            css_vars.append("")
        
        css_vars.append("}")
        return "\n".join(css_vars)

# Example usage
if __name__ == "__main__":
    converter = PantoneRGBConverter()
    
    # Print the complete palette with color swatches
    converter.print_palette()
    
    print("\n" + "=" * 60)
    print("ADDITIONAL VISUALIZATION OPTIONS")
    print("=" * 60)
    
    # Show available visualization methods
    if PIL_AVAILABLE:
        print("✅ PIL available - can create palette image")
        response = input("Create palette image? (y/n): ").lower()
        if response == 'y':
            converter.create_color_palette_image()
    else:
        print("❌ PIL not available - install with: pip install Pillow")
    
    if MATPLOTLIB_AVAILABLE:
        print("✅ Matplotlib available - can create interactive palette")
        response = input("Create matplotlib palette? (y/n): ").lower()
        if response == 'y':
            converter.create_matplotlib_palette()
    else:
        print("❌ Matplotlib not available - install with: pip install matplotlib")
    
    print("\n" + "=" * 60)
    print("CSS CUSTOM PROPERTIES")
    print("=" * 60)
    print(converter.get_css_variables())

# Installation instructions
print("\n" + "=" * 60)
print("INSTALLATION INSTRUCTIONS")
print("=" * 60)
print("For best color display, install optional packages:")
print("pip install Pillow matplotlib colorama")
print("=" * 60)