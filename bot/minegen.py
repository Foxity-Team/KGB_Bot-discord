import random

FIELD_EMOJI_MAP = {
    -1: '🅱️',
    0: '0️⃣',
    1: '1️⃣',
    2: '2️⃣',
    3: '3️⃣',
    4: '4️⃣',
    5: '5️⃣',
    6: '6️⃣',
    7: '7️⃣',
    8: '8️⃣',
    9: '9️⃣',
}

def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min(value, max_value), min_value)

class Field:
    def __init__(self, width: int, height: int, mine_count: int) -> None:
        if width <= 0 or height <= 0 or mine_count <= 0:
            raise ValueError('Supplied negative integers for mine field')

        self._width = width
        self._height = height
        self._mine_count = _clamp(mine_count, 1, self._width * self._height)

        self._field = self.generate()

    def generate(self) -> list[list[int]]:
        mine_field = [[0 for _ in range(self._height)] for _ in range(self._width)]
        
        mines_left = self._mine_count
        while mines_left > 0:
            x = random.randrange(self._width)
            y = random.randrange(self._height)
            
            if mine_field[x][y] == -1: continue

            mine_field[x][y] = -1
            mines_left -= 1

        for i in range(self._width):
            for j in range(self._height):
                if mine_field[i][j] == -1: continue
                mine_field[i][j] = self.check_surround(i, j, mine_field)

        return mine_field

    def check_surround(self, x: int, y: int, mine_field: list[list[int]]) -> int:
        neighbors = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0: continue
                if x+i < 0 or y+j < 0 or x+i > self._width - 1 or y+j > self._height - 1: continue
                if mine_field[x+i][y+j] != -1: continue
                neighbors += 1

        return neighbors

    def __str__(self) -> str:
        out = ''
        for j in range(self._height):
            line = ''
            for i in range(self._width):
                cell = self._field[i][j]
                line += f'||{FIELD_EMOJI_MAP[cell]}||'
            out += line + '\n'
        return out

if __name__ == '__main__':
    field = Field(11, 11, 10)
    print(field)
