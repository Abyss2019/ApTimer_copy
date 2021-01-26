from rest_framework.response import Response
from rest_framework import views

from .forms import ExcelForm, InputIniboundForm
from .serializers import DiffSerializers, IniBoundSerializers, DisTimeSerializers

from .calculation.diffusivity import DiffFunc
from .calculation.inibound import IniBound
from .calculation.distime import DisTime

import numpy as np


class ExcelView(views.APIView):
    def post(self, request):
        form = ExcelForm(request.POST, request.FILES)
        excel = request.FILES['excel']
        if form.is_valid():
            meas_dis = []
            lines = excel.readlines()
            length = len(lines) - 1
            meas_profile = np.zeros((3, length))    # array 3x19
            err = np.zeros((3, length))             # array 3x19
            i = 0
            for line in lines[1:]:
                meas_dis.append(i)
                line = line.decode('utf-8').split(',')
                print(line)
                meas_profile[:, i] = np.array(line[1:4])
                err[:, i] = np.array(line[4:7])
                i += 1
            x = meas_dis
            y_cl = meas_profile[0, :]
            y_f = meas_profile[1, :]
            y_oh = meas_profile[2, :]
            err_cl = err[0]
            err_f = err[1]
            err_oh = err[2]

        return Response({
            'name': excel.name,
            'x': x,
            'y_cl': y_cl,
            'y_f': y_f,
            'y_oh': y_oh,
            'err_cl': err_cl,
            'err_f': err_f,
            'err_oh': err_oh,
            'length': length-1,
        })

class InputIniboundView(views.APIView):
    def post(self, request):
        form = InputIniboundForm(request.POST, request.FILES)
        input_file = request.FILES['file']
        if form.is_valid():
            lines = input_file.readlines()
            xcl_input = map(lambda x: float(x), filter(lambda x: x, lines[1].decode('utf-8').split(',')[1:]))
            xf_input = map(lambda x: float(x), filter(lambda x: x, lines[2].decode('utf-8').split(',')[1:]))
            xoh_input = map(lambda x: float(x), filter(lambda x: x, lines[3].decode('utf-8').split(',')[1:]))

        return Response({
            "xcl": xcl_input,
            "xf": xf_input,
            "xoh": xoh_input,
        })


class DiffView(views.APIView):
    def get(self, request):
        serializer = DiffSerializers(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        diffusivity = DiffFunc(data).diffusivity()

        return Response({
            "diffusivity": diffusivity,
        })


class IniBoundView(views.APIView):
    def get(self, request):
        serializer = IniBoundSerializers(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        inibound = IniBound(data).show_input()
        return Response({
            "inibound_cl": inibound['xcl'],
            "inibound_f": inibound['xf'],
            "inibound_oh": inibound['xoh'],
        })


class DisTimeView(views.APIView):
    def get(self, request):
        serializer = DisTimeSerializers(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        distime = DisTime(data).show_input()['result']
        if distime['state'] == 'no best fit':
            return Response({
                'state': distime['state'],
                'x': distime['x'],
                'red_cl': distime['red_cl'],
                'red_f': distime['red_f'],
                'red_oh': distime['red_oh'],
                'min_Ans': distime['min_Ans'],
                'max_Ans': distime['max_Ans'],
                'best_fit_time': distime['best_fit_time'],
                'best_day': distime['best_day'],
                'plus': distime['plus'],
                'minus': distime['minus'],
                })
        else:
            return Response({
                    'state': distime['state'],
                    'x': distime['x'],
                    'red_cl': distime['red_cl'],
                    'red_f': distime['red_f'],
                    'red_oh': distime['red_oh'],
                    'min_Ans': distime['min_Ans'],
                    'max_Ans': distime['max_Ans'],
                    'best_fit_time': distime['best_fit_time'],
                    'best_day': distime['best_day'],
                    'plus': distime['plus'],
                    'minus': distime['minus'],
            })
