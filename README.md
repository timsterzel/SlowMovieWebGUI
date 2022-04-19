# SlowMovie Web GUI
A GUI frontend to control [SlowMovie Player](https://github.com/TomWhitwell/SlowMovie) for E-Paper Displays on a raspberry pi.
  
Goal of the project is to provide a web interface, accessible within the same network to control SlowMovie running on your raspberry pi.  
  
The project is still in a very early state and not stable yet.

## Details
To provide the web interface and comunicate with the python application on your raspberry pi the project uses [eel](https://github.com/ChrisKnott/Eel) as framework.
At frontend level HTML with [Tailwindcss](https://tailwindcss.com/) is used to create the interface.  
Tailwindcss is already included inside the project. But you have to install eel to run the application:  
```
pip install eel
```
Additionally it is necesarry to rename ```config.py.example``` to ```config.py``` and specify your raspberrypi's local ip and the port you want to use to access the web interface.  
Also you have to configurate the location of the SlowMovie application and the directory of the Videos played by SlowMovie.  
  
SlowMovie is started as subprocess within the python script.  

To start SlowMovie Web GUI:  
```
python3 slowmovie_web_gui.py
```

## Implementation Details
The implementation and control of SlowMovie is realizied without any modification of the SlowMovie code. Instead SlowMovie Web GUI is a wrapper around the SlowMovie command line application. SlowMovie is controlled by stopping and restarting the application with the right command line arguments. The current progress is parsed from the application Info and Debug output. As parsing application output usually isn't a recommended way of retrieving data, this future might break when new SlowMovie Versions are out. But for now it is working and seem to be a sufficient way to get the information needed, without forking and modyfing SlowMovie.
  
If you are looking for a more stable way to play and control played movies take a look at [VSMP+ (Very Slow Media Player Plus)](https://github.com/robweber/vsmp-plus) as SlowMovie alternative.


## Current frontend screenshots
![Play](/images/Play.jpg "Play.jpg")  
![Progress](/images/Progress.jpg "Progress.jpg")

## ToDo:
- Make application run as service
- Optimize web interface (especially on mobile devices)

