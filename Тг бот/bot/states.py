class ObjectStates:
    NAME = 1
    ADDRESS = 2
    EXTERNAL_ID = 3
    CONFIRM = 4

class WorkTypeStates:
    NAME = 10
    UNIT = 11
    LABOR_COST = 12
    CONFIRM = 13

class MaterialStates:
    NAME = 20
    UNIT = 21
    PRICE = 22
    CONFIRM = 23

class NormStates:
    SELECT_WORK_TYPE = 30
    SELECT_MATERIAL = 31
    QUANTITY = 32
    CONFIRM = 33

class TaskStates:
    SELECT_NETWORK = 40
    INPUT_ADDRESS = 41
    SELECT_WORK_TYPE = 42
    INPUT_AREA = 43
    INPUT_MATERIAL_PRICES = 44
    INPUT_LABOR_COST = 45
    SHOW_CALCULATION = 46
    CONFIRM_SAVE = 47
    INPUT_PROFILE_STEP = 48
    INPUT_PROFILE_TYPE = 49
    INPUT_DOOR = 50
    INPUT_DOOR_DIMENSIONS = 51
    INPUT_DOOR_HEIGHT = 52

class PurchaseStates:
    SELECT_TASK = 50
    SELECT_MATERIAL = 51
    TOGGLE_PURCHASED = 52
    INPUT_ACTUAL_COST = 53

class FinanceStates:
    SELECT_OBJECT = 60
    SELECT_TASK = 61

class SetPriceStates:
    SELECT_WORK_TYPE_COST = 80
    INPUT_WORK_TYPE_COST = 81