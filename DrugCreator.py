import PySimpleGUI as gui
from threading import Thread
from json import dumps
from os import getcwd, path
from ResourcePath import resource_path

def make_window():
    gui.theme('Light Blue 3')
    layout = [
                [gui.Col([[gui.Col([[gui.Text('Name:', size=(5,1)), gui.Input('', size=(15, 1), enable_events=True, key='NAME')]])]])],
                [gui.Col([[gui.Col([[gui.Text('Unit:', size=(5,1)), gui.Input(size=(3, 1), default_text='mg', justification='right', enable_events=True, key='UNIT')]])]])],
                [gui.Col([add_row(0), add_row(1)], key='SIZES')],
                [gui.Col([[gui.Col([[gui.pin(gui.Button("Add", enable_events=True, key='ADD', bind_return_key=True)), gui.Button("Save", bind_return_key=True, enable_events=True, key='SAVE')]])]])]
    ]
    window = gui.Window('Drug Creator', font=('_ 15'), icon=(resource_path('Resources/needle.ico')), layout=layout, finalize=True, modal=True, resizable=True, element_justification='l', metadata=1)
    return window

def add_row(index):
    row = [gui.pin(gui.Col([ [ gui.Text('Size:', size=(5,1)),
                               gui.Input(size=(5,1), enable_events=True, default_text=0, justification='right', key=('SIZE', index)),
                               gui.Button(gui.SYMBOL_X, border_width=0, key=('DEL', index))] ], key=('ROW', index) ) )
           ]
    return row

def getVisibleCount(window: gui.Window):
    visible = 0
    for row in range(window.metadata+1):
        if window[('ROW', row)].visible:
            visible += 1
    return visible

def main():
    window = make_window()
    while(True):
        event, values = window.read()
        if event in (gui.WIN_CLOSED, 'Exit'):
            break
        elif event in ('NAME', 'UNIT'):
            if values[event] and not str(values[event][-1]).isalpha():
                window[event].update(values[event][:-1]) #reset to previous string before invalid character was entered
        elif event == 'ADD':
            vis = getVisibleCount(window)
            if vis < 5:
                window.metadata += 1
                window.extend_layout(window['SIZES'], [add_row(window.metadata)])
        elif isinstance(event, tuple):
            if event[0] == 'DEL' and getVisibleCount(window) > 1:
                window[('ROW', event[1])].update(visible=False)
            elif event[0] == 'SIZE':
                if values[(event[0], event[1])] and not str(values[(event[0], event[1])][-1]).isnumeric():
                    window[event].update(values[(event[0], event[1])][:-1])
        elif event == 'SAVE':
            name = window['NAME'].get().lower().capitalize()
            unit = window['UNIT'].get()
            sizes = []
            for row in range(window.metadata + 1):
                if not window[('ROW', row)].visible:
                    continue
                else:
                    sizes.append(int(window[('SIZE', row)].get()))
            checkInputs(window, name, unit, sizes)
        elif event == 'ERROR':
            gui.popup_ok(values[event], modal=True, font=('_ 15'), keep_on_top='True', title='Error', icon=(resource_path('Resources/needle.ico')))
        elif event == 'EXPORT':
            Thread(target=saveDrug, args=(window, *values[event]), daemon=True).start()
        elif event == 'MSG':
            gui.popup_auto_close(values[event], auto_close_duration=3, modal=True, font=('_ 15'), keep_on_top='True', title='File Saved', icon=(resource_path('Resources/needle.ico')))
            window.write_event_value('Exit', '')
    window.close()

def saveDrug(window: gui.Window, name, unit, sizeList):
    drug = {"name": name,
        "sizes": sizeList,
        "unit": unit
    }

    data = dumps(drug, indent=4)
    loc = path.normpath(getcwd() + "\\Drugs\\")
    # print(loc)
    with open(str(loc + '\\' + drug['name'] + ".json"), "w") as file:
        file.write(data)
    # print('Saved file')
    window.write_event_value('MSG', 'File was saved successfully.')

def checkInputs(window: gui.Window, name: str, unit: str, sizes: list):
    ret = True
    if not name:
        window.write_event_value('ERROR', 'Name field cannot be blank')
        ret = False
    if not unit:
        window.write_event_value('ERROR', 'Unit field cannot be blank')
        ret = False
    if (0 in sizes):
        window.write_event_value('ERROR', 'Size fields must contain a value larger than \'zero\'')
        ret = False
    if len(sizes) != len(set(sizes)):
        window.write_event_value('ERROR', 'Size fields contain duplicate values.')
        ret = False
    if ret == True:
        window.write_event_value('EXPORT', [name, unit, sizes])

if __name__ == '__main__':
    main()
