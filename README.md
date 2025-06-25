# Portfolio-CS-350
Project Summary:
This project was about building a working prototype for a smart thermostat system that could later be connected to the cloud. The goal was to create software that uses an AHT20 temperature sensor, several GPIO buttons and LEDs, an LCD display, and UART communication. I wrote the code in Python to read the temperature, control the LEDs, detect button presses, manage the thermostat’s modes through a state machine, and show updates on the LCD. The system also sent data over the serial port to simulate cloud communication and helped decide which hardware architecture would work best for future development.

What I Did Well:
I’m proud of how well I got the state machine working. Each state (off, heat, cool) functioned correctly, and the button presses triggered state changes without issues. The display updated smoothly, which made it easier to track what the system was doing. I kept the code organized by using threads and separate functions for each part, which made it more readable and easier to troubleshoot.

Where I Could Improve:
One thing I could do better is planning out hardware testing. I ran into some trouble with getting the I2C sensor and UART communication working at first. In the future, I would test each piece of hardware by itself before putting everything together. I would also build in better error handling from the start.

Resources and Tools Added:
I learned how to use the gpiozero library more effectively and how to set up UART on the Raspberry Pi. I also started using the statemachine module in Python, which made handling the thermostat modes simpler. I added draw.io to my list of tools for designing diagrams, which helped me build and share the state machine.

Transferable Skills:
This project helped me get better at writing code that works directly with hardware, handling input in real time, and keeping embedded software well-structured. These skills will help in future projects, especially anything involving IoT devices, robotics, or low-level programming.

Project Maintainability:
I kept the code easy to maintain by organizing it into sections, using clear names, and adding helpful comments. I separated hardware setup from the main logic, so it would be simple to update the code if the hardware changes. Using threads and a clean state machine also made the behavior of the thermostat easier to follow and adjust.
