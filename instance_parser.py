import sys
from pprint import pprint
import neal
import scheduler
from dwave.system.samplers import DWaveSampler
from dwave.system.composites import EmbeddingComposite
#from dwave.system import chain_strength



class Nurse:

    def __init__(self, maxShifts, maxTotalMinutes, minTotalMinutes,
                 maxConsecutiveShifts, minConsecutiveShifts,
                 minConsecutiveDaysOff, maxWeekends):
        self.maxShifts = maxShifts  # {D: 14, E: 10}
        self.maxTotalMinutes = maxTotalMinutes
        self.minTotalMinutes = minTotalMinutes
        self.maxConsecutiveShifts = maxConsecutiveShifts
        self.minConsecutiveShifts = minConsecutiveShifts
        self.minConsecutiveDaysOff = minConsecutiveDaysOff
        self.maxWeekends = maxWeekends


class Shift:
    def __init__(self, length, not_before):
        self.length = length
        self.not_before = not_before


def parse(path):
    """
    {
        D: (400, (A, B, C))
    }
    """
    shift_types = {}
    staff = {}
    daysOff = {}
    shiftsOnRequests = []
    shiftsOffRequests = []
    cover = []
    section = ""
    with open(path) as f:
        for line in f:
            line = line[:-1]  # throwing \n char out
            if line.startswith("#") or line == "":
                continue
            if line.startswith("SECTION"):
                section = line
                continue
            if section == "SECTION_HORIZON":
                horizon_len = int(line)
            if section == "SECTION_SHIFTS":
                shift_data = line.split(',')
                # shifts which cannot FOLLOW THIS SHIFT
                not_before = shift_data[2].split('|')
                shift_types[shift_data[0]] = Shift(shift_data[1], not_before)

            if section == "SECTION_STAFF":
                staff_data = line.split(',')
                max_shifts_data = staff_data[1].split('|')
                max_shifts = {x.split('=')[0]: int(x.split('=')[1])
                              for x in max_shifts_data}
                # TODO: sprawdz czy da sie bez list
                staff[staff_data[0]] = Nurse(
                    max_shifts, *map(int, staff_data[2:]))

            if section == "SECTION_DAYS_OFF":
                employee, *days = line.split(',')
                daysOff[employee] = days
            if section == "SECTION_SHIFT_ON_REQUESTS":
                request = line.split(',')
                # employee, day, shift, weight = line.split(',')
                shiftsOnRequests.append(request)
            if section == "SECTION_SHIFT_OFF_REQUESTS":
                request = line.split(',')
                shiftsOffRequests.append(request)
            if section == "SECTION_COVER":
                cover.append(line.split(','))
    return shift_types, staff, horizon_len


if __name__ == "__main__":
    path = "./instances1_24/Instance_my.ros"
    shift_types, nurses, horizon = parse(path)
    qpu = False

    if qpu:
        sampler = EmbeddingComposite(
            DWaveSampler(solver={'qpu': True}))
    else:
        sampler = neal.SimulatedAnnealingSampler()

    bqm = scheduler.get_bqm(shift_types, nurses, horizon,
                            stitch_kwargs={'min_classical_gap': 1})

    if qpu:
        sampleset = sampler.sample(
            bqm, chain_strength=sampler.chain_strength, num_reads=1000)
    else:
        sampleset = sampler.sample(bqm, num_reads=1000)

    solution1 = sampleset.first.sample
    print(solution1)
