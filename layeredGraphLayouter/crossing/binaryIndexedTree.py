class BinaryIndexedTree():
    """
    :note: Ported from ELK.

    Sorted list of integers storing values from 0 up to the maxNumber passed
    on creation. Adding, removing and indexOf
    (and addAndIndexOf) is in O(log maxNumber).

    Implemented as a binary tree where each leaf stores the number of integers
    at the leaf index and each node stores the
    number of values in the left branch of the node.
    """

    def __init__(self, maxNum: int):
        """
        :param maxNum: maximum number elements.
        """
        self.maxNum = maxNum
        self.binarySums = [0 for _ in range(maxNum + 1)]
        self.numsPerIndex = [0 for _ in range(maxNum)]
        self.size = 0
        self.fill_with_zero = True

    def extend_size(self, newMaxNum: int):
        toAdd = newMaxNum - self.maxNum
        if toAdd > 0:
            newItems = [0 for _ in range(toAdd)]
            self.binarySums.extend(newItems)
            self.numsPerIndex.extend(newItems)

    def add(self, index: int):
        """
        Increment given index.
        :param index: The index to increment.
        """
        try:
            self.numsPerIndex[index] += 1
        except IndexError:
            if self.fill_with_zero:
                self.extend_size(index + 1)
                return self.add(index)
            else:
                raise

        self.size += 1
        i = index + 1
        binarySums = self.binarySums
        len_ = len(binarySums)
        while i < len_:
            binarySums[i] += 1
            i += i & -i

    def rank(self, index: int):
        """
        Sum all entries before given index, i.e. index - 1.

        :param index: Not included end index.
        :return sum:
        """
        sum_ = 0
        binarySums = self.binarySums
        while index > 0:
            try:
                sum_ += binarySums[index]
            except IndexError:
                if not self.fill_with_zero:
                    raise

            index -= index & -index

        return sum_

    def size(self):
        return self.size

    def removeAll(self, index: int):
        """
        Remove all entries for one index.

        :param index: the index
        """
        try:
            numEntries = self.numsPerIndex[index]
        except IndexError:
            print(index)
            raise
        if numEntries == 0:
            return

        self.numsPerIndex[index] = 0
        self.size -= numEntries
        i = index + 1
        binarySums = self.binarySums
        while i < len(binarySums):
            binarySums[i] -= numEntries
            i += i & -i

    def clear(self):
        """
        Clears contents of tree.
        """
        binarySumsLen_ = len(self.binarySums)
        numsPerIndex_ = len(self.numsPerIndex)

        self.binarySums = [0 for _ in range(binarySumsLen_)]
        self.numsPerIndex = [0 for _ in range(numsPerIndex_)]
        self.size = 0

    def isEmpty(self) -> bool:
        return self.size == 0
