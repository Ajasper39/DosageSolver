import PySimpleGUI as gui
from docplex.mp.model import Model
from json import load
from os import getcwd, path, listdir, mkdir
from threading import Thread
from DrugCreator import main as drugCreator
from ResourcePath import resource_path

DICT = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E'}
FILES = []
TABLEDATA = [['        '],['   ']]
HEADINGS = ['Size', 'Qty']

def doseSolverGui():

    gui.theme('Light Green 3')
    guiLayout = [
        [gui.Text('Drug:'), gui.Combo(['None'],  size=(15, 0), readonly=True, bind_return_key=True, enable_events=True, key='DRUG')],
        [gui.Text('Dose:'), gui.Input(justification='right', default_text=0, size=(6, 1), key='DOSE', enable_events=True, metadata=0), gui.Text('mg', key='DRUG_UNITS', enable_events=True)],
        [gui.Button('Solve', disabled=True, enable_events=True, key='SOLVE', bind_return_key=True)],
        [gui.Table(values=TABLEDATA, headings=HEADINGS, col_widths=[10, 3], display_row_numbers=False, auto_size_columns=True, num_rows=5, visible=True, hide_vertical_scroll=True, key='TABLE')],
        [gui.Text('Waste:'), gui.Text('0', enable_events=True, key='WASTE'), gui.Text('mg', key='WASTE_UNITS', enable_events=True)],
        [gui.Button('Add Drug', enable_events=True, key='ADD'), gui.Button('Refresh', enable_events=True, bind_return_key=False, key='FIND')]
    ]

    window = gui.Window('Dosage Solver', size=(400, 350), resizable=True, icon=resource_path('Resources/needle.ico'), element_justification='center', layout=guiLayout, finalize=True, font=('_ 15'))

    window.write_event_value('FIND', '')

    while(True):
        event, ret = window.Read()
        if event == gui.WIN_CLOSED or event is None:
            break
        elif event == 'DOSE':
            if str(ret[event]).isnumeric() or ret[event] == '':
                window[event].metadata = ret[event]
            else:
                window[event].update(window[event].metadata)
        elif event == 'FIND':
            Thread(target=getFiles, args=(window, drugsPath()), daemon=True).start()
        elif event == 'FILE':
            Thread(target=getNames, args=(window, ret[event]), daemon=True).start()
        elif event == 'LIST':
            window['DRUG'].update(value=ret[event][0], values=ret[event])
            window['SOLVE'].update(disabled=False)
            window.write_event_value('DRUG', ret[event][0])
        elif event == 'SOLVE':
            dose = (lambda: int(ret['DOSE']), lambda: 0)[ret['DOSE'] == '']()
            name = str(window['DRUG'].metadata['name'])
            sizes = sorted(window['DRUG'].metadata['sizes'], reverse=True)
            unit = str(window['DRUG'].metadata['unit'])
            Thread(target=solveDose, args=(window, name, dose, sizes, unit), daemon=True).start()
        elif event == 'TABLE':
            window[event].update(values=ret[event])
        elif event == 'WASTE':
            window[event].update(value=('{0}'.format(ret[event])))
        elif event == 'ADD':
            Thread(target=drugCreator(), daemon=True).start()
        elif event == 'UNITS':
            window['DRUG_UNITS'].update(value='{0}'.format(ret[event]))
            window['WASTE_UNITS'].update(value='{0}'.format(ret[event]))
        elif event == 'DRUG':
            window.write_event_value('CLEAR', '')
            Thread(target=readDrugInfo, args=(window, ret['DRUG'], drugsPath()), daemon=True).start()
        elif event == 'CLEAR':
            window['TABLE'].update(values=TABLEDATA)
            window['WASTE'].update(value=0)
            window['DOSE'].update(value=0)

def drugsPath():
    try:
        dir = path.normpath(getcwd() + "\\Drugs")
        if not path.exists(dir):
            raise FileNotFoundError
    except FileNotFoundError:
        mkdir(dir)
    finally:
        return dir

def getFiles(window: gui.Window, loc: path):
    files = []
    if path.isdir(loc):
        files += [path.normpath(loc + "\\" + file) for file in listdir(loc) if file.endswith('.json')]

    if len(files) == 0:
        files += ['None']
    # print(files)
    window.write_event_value('FILE', files)

def getNames(window: gui.Window, files: list):
    names = []
    for file in files:
        names += [str(file.split("\\")[-1]).replace('.json', '')]
    # print(names)
    window.write_event_value('LIST', names)

def readDrugInfo(window: gui.Window, name: str, loc: path):
    try:
        filePath = path.normpath(loc + "\\" + name + '.json')
        if path.exists(filePath):
            with open(filePath, 'r') as file:
                data = load(file)
                window['DRUG'].metadata = data
                # print(window['DRUG'].metadata['unit'])
                window.write_event_value('UNITS', window['DRUG'].metadata['unit'])
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        window['SOLVE'].update(disabled=True)

def solveDose(window: gui.Window, name: str, dose: int, sizes: list, unit: str):

    objFn = 0
    vars = []
    answer = []
    values = {}
    waste = 0

    prob = Model(name=name)

    for i, size in enumerate(sizes):
        vars += [prob.integer_var(name=DICT[i], lb=0, ub=size)]
        objFn = sum([objFn, vars[i] * size])

    prob.add_constraint(objFn >= dose)
    prob.set_objective('min', objFn)

    result = prob.solve()
    result = str(result).splitlines()

    for i, value in enumerate(result):
        match(i):
            case 0:
                continue #solution name
            case 1:
                waste = int(value.split(':')[-1]) - dose #solution objective
            case 2:
                continue #solution status
            case _:
                var = value.split('=')
                values.update({str(var[0]) : int(var[1])})

    for i in range(len(sizes)):
        temp = (lambda: values.get(str(DICT[i])), lambda: 0)[values.get(str(DICT[i])) == None]()
        answer += [[str(sizes[i]) + str(unit), temp]]

    # print(values)
    # print(answer)
    # print(waste)

    window.write_event_value('TABLE', answer)
    window.write_event_value('WASTE', waste)

if __name__ == '__main__':
    doseSolverGui()