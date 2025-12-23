# Hazard Ball: Escape the Grid

**Hazard Ball** is a 3D survival puzzle game built using Python and OpenGL. Your objective is to navigate a treacherous, procedurally generated grid, collect energy cores, and activate the portal to escape before you run out of lives.

## 🚀 How to Run
Ensure you have Python installed along with the required PyOpenGL libraries.

```bash
pip install PyOpenGL PyOpenGL_accelerate
python hazardball.prev.py
```

## 🎮 Controls
*   **W, A, S, D**: Move the ball (Discrete movement).
*   **Arrow Keys**: Rotate and zoom the camera.
*   **Right Click**: Toggle between **Third-Person** and **First-Person** view.
*   **R**: Restart the game (Resets to Level 1).

## 🏆 Gameplay & Levels
The game features an escalating difficulty curve across **5 Levels**:

1.  **Level 1: The Surface** - Standard grid with static holes and obstacles. Collect **5 Cores** (Diamonds) to open the portal.
2.  **Level 2: The Depths** - Increased density of holes and obstacles.
3.  **Level 3: Kinetic Walls** - Introduces **Moving Walls** (Pulsing Red) that patrol the grid. They will push you if you collide!
4.  **Level 4: Shifting Ground** - Introduces **Moving Holes** (Pulsing Purple). Watch the yellow guide lines to avoid falling into the void.
5.  **Level 5: Meltdown** - The grid is unstable! Every few seconds, random safe tiles near you will crumble into holes. Speed is essential.

### Items
*   **Cyan Diamond**: Energy Core (Collect 5 to unlock Portal).
*   **Magenta Sphere**: Speed Boost (Doubles speed for limited time).
*   **Green Cube**: Extra Life.

## 🔧 Technical Overview
This project uses **legacy OpenGL (Immediate Mode)** and **GLUT** for rendering and window management.

*   **Render Loop**: The `showScreen()` function clears the buffer, sets up the camera (`gluLookAt`), and calls drawing helpers.
*   **Procedural Generation**: `init_map()` generates a dictionary-based grid map (`map_data`), randomly assigning tiles as Floor, Hole, Obstacle, or Item based on the current Level difficulty.
*   **Physics**: Simple collision detection (`check_collisions`) handles AABB interactions for static blocks and "Sphere-vs-AABB" logic for the player. Moving objects update their positions in `idle()`.
*   **State Management**: Global variables track game state (Level, Score, Lives, Object Lists).


