import PySimpleGUI as gui
from json import load
from os import getcwd, path, listdir
from threading import Thread
from pulp import LpMinimize, LpProblem, LpInteger, LpVariable, PULP_CBC_CMD
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
            sizes = window['DRUG'].metadata['sizes']
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
    return path.normpath(getcwd() + "\\Drugs")

def getFiles(window, loc):
    files = []
    if path.isdir(loc):
        files += [path.normpath(loc + "\\" + file) for file in listdir(loc) if file.endswith('.json')]
    # print(files)
    window.write_event_value('FILE', files)

def getNames(window, files):
    names = []
    for file in files:
        names += [str(file.split("\\")[-1]).replace('.json', '')]
    # print(names)
    window.write_event_value('LIST', names)

def readDrugInfo(window: gui.Window, name, loc):
    filePath = path.normpath(loc + "\\" + name + '.json')
    with open(filePath, 'r') as file:
        data = load(file)
    window['DRUG'].metadata = data
    # print(window['DRUG'].metadata['unit'])
    window.write_event_value('UNITS', window['DRUG'].metadata['unit'])

def solveDose(window, name, dose, sizes, unit):

    objFn = None
    vars = []
    answer = []

    prob = LpProblem(name, LpMinimize)

    for i, size in enumerate(sizes):
        vars += [LpVariable(DICT[i], 0, cat=LpInteger)]
        objFn += (vars[i] * size)

    # print(vars)
    # print(objFn)
    constraint = (objFn >= dose)

    prob += objFn
    prob += constraint

    prob.solve(PULP_CBC_CMD(msg=0))

    for i in range(len(sizes)):
        answer += [[str(str(sizes[i]) + str(unit)), int(vars[i].varValue)]]

    waste = int(abs(prob.objective.value() - dose))

    # print(answer)
    # print(dict(zip(sizes, values)))
    # print(waste)

    window.write_event_value('TABLE', answer)
    window.write_event_value('WASTE', waste)

if __name__ == '__main__':
    doseSolverGui()