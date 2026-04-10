#!/usr/bin/env python3
"""
Interactive Dynamic Surface Demo
Demonstrates the new interactive time slider functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynamic_surface import DynamicSurface
import numpy as np

def demo_interactive_slider():
    """Demonstrate the interactive time slider feature"""

    # Define a more interesting dynamic surface function
    def complex_wave_surface(x, y, t):
        """Complex wave surface with multiple patterns"""
        # Primary wave from center
        wave1 = np.sin(np.sqrt(x**2 + y**2) - 2*t) * np.exp(-0.05*t)
        # Secondary wave pattern
        wave2 = 0.5 * np.cos(2*x - 3*t) * np.sin(2*y + t) * np.exp(-0.02*t)
        # Combine waves
        return wave1 + wave2

    # Create dynamic surface instance
    ds = DynamicSurface(complex_wave_surface)

    # Set ranges
    x_range = (-6, 6)
    y_range = (-6, 6)
    t_range = (0, 15)

    print("=" * 60)
    print("Interactive Dynamic Surface Demo")
    print("=" * 60)
    print()
    print("This demo showcases a dynamic surface with interactive time control.")
    print("You can:")
    print("- Drag the time slider at the bottom to see the surface evolve")
    print("- Rotate the 3D view by clicking and dragging")
    print("- Zoom using the mouse wheel")
    print()
    print("The surface function combines:")
    print("- A primary radial wave from the center")
    print("- A secondary wave pattern")
    print("- Exponential decay over time")
    print()
    print("Time range: 0 to 15")
    print("=" * 60)
    print()

    # Launch the interactive visualization with time slider
    ds.interactive_surface_with_slider(x_range, y_range, t_range, resolution=40)

if __name__ == "__main__":
    demo_interactive_slider()