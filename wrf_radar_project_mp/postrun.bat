rem python filter_top.py E:\wrf3.6.1\ARWH_KainFritschCu_Morrison\reflec_netcdf
rem python filter_top.py E:\wrf3.6.1\ARWH_KainFritschCu_WDM6\reflec_netcdf
rem python filter_top.py E:\wrf3.6.1\ARWH_KainFritschCu_WSM6\reflec_netcdf
rem python filter_top.py E:\wrf3.6.1\ARWH_TiedtkeCu_Morrison\reflec_netcdf
rem python filter_top.py E:\wrf3.6.1\ARWH_TiedtkeCu_WDM6\reflec_netcdf
rem python filter_top.py E:\wrf3.6.1\ARWH_TiedtkeCu_WSM6\reflec_netcdf

rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_KainFritschCu_Morrison\reflec_netcdf\top_1
rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_KainFritschCu_WDM6\reflec_netcdf\top_1
rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_KainFritschCu_WSM6\reflec_netcdf\top_1
rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_TiedtkeCu_Morrison\reflec_netcdf\top_1
rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_TiedtkeCu_WDM6\reflec_netcdf\top_1
rem python aggregate_dbf.py E:\wrf3.6.1\ARWH_TiedtkeCu_WSM6\reflec_netcdf\top_1

C:\Python27\ArcGIS10.4\python.exe filter_top.py D:\isabel_wrf_restart\windfield\KFS
C:\Python27\ArcGIS10.4\python.exe aggregate_dbf.py D:\isabel_wrf_restart\windfield\KFS\top_1

C:\Python27\ArcGIS10.4\python.exe filter_top.py D:\isabel_wrf_restart\windfield\zTS
C:\Python27\ArcGIS10.4\python.exe aggregate_dbf.py D:\isabel_wrf_restart\windfield\zTS\top_1

C:\Python27\ArcGIS10.4\python.exe filter_top.py D:\isabel_wrf_restart\windfield\TS
C:\Python27\ArcGIS10.4\python.exe aggregate_dbf.py D:\isabel_wrf_restart\windfield\TS\top_1