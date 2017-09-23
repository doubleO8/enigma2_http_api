=================== =================== =================== ===================
EEvent attribute    epg                 timer               movie              
=================== =================== =================== ===================
duration [#f2]_     duration_sec        -- n/a --           length             
item_id             id                  eit                 -- n/a --          
longinfo            longdesc            descriptionextended descriptionExtended
service_name        sname               servicename         servicename        
service_reference   sref                serviceref          serviceref         
shortinfo           shortdesc           description         description        
start_time [#f1]_   begin_timestamp     begin               recordingtime      
stop_time [#f1]_    -- n/a --           end                 -- n/a --          
title               title               name                eventname          
=================== =================== =================== ===================

.. rubric:: Footnotes
.. [#f1] :py:class:`datetime.datetime` instances.
.. [#f2] :py:class:`datetime.timedelta` instances.