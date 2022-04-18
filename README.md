# E-PaperHub
A GUI frontend to control multiple e-paper applications, running on a raspberry pi with python.
  
Goal of the project is to provide a web interface, accessible within the same network to control multiple e-Paper applications running on your raspberry pi e-Paper device (For example Raspberry pi with a Waveshare e-paper display).  
  
The project is still in a very early state and not stable yet. At the moment only the [SlowMovie](https://github.com/TomWhitwell/SlowMovie) application is supported, but more applications will follow in the future.  

## Details
To provide the web interface and comunicate with the python application on your raspberry pi the project uses [eel](https://github.com/ChrisKnott/Eel) as framework.
At frontend level [Tailwindcss](https://tailwindcss.com/) is used to style the interface.  
Tailwindcss is already included inside the project. But you have to install eel to run the application:  
```
pip install eel
```
Additionally it is necesarry to rename ```config.py.example``` to ```config.py``` and specify your raspberrypi's local ip and the port you want to use to access the web interface.
Also you have to configurate the location of the SlowMovie application and the directory of the Videos played by SlowMovie.  
  
Applications started by E-PaperHub are started as subprocess within the python script.  

To start E-PaperHub:  
```
python3 E-PaperHub.py
```

## SlowMovie implementation
The implementation and control of SlowMovie is realizied without any modification of the SlowMovie code. Instead SlowMovie is controlled by stopping and restarting the application with the right command line arguments. The current progress is parsed from the application Info and Debug output. As parsing application output usually isn't a recommended way of retrieving data, this future might break when new SlowMovie Versions are out. But for now it is working and seem to be a sufficient way to get the information needed, without forking SlowMovie.
  
If you only want to control and run SlowMovie and no other applications [VSMP+ (Very Slow Media Player Plus)](https://github.com/robweber/vsmp-plus) might be a better (and currently more stable) solution.  

## Compatible applications
- [SlowMovie](https://github.com/TomWhitwell/SlowMovie)

## Current frontend screenshots
![Play](/images/Play.jpg "Play.jpg")  
![Progress](/images/Progress.jpg "Progress.jpg")

## ToDo:
- Make application run as service
- Make application modular to make it easy for everyone to create custom modules for other e-paper applications
- Optimize web interface (especially on mobile devices)
- Much more
