=================== =================== ===================
EEvent attribute    epg                 timer              
=================== =================== ===================
duration [#f2]_     duration_sec        -- n/a --          
item_id             id                  eit                
longinfo            longdesc            descriptionextended
service_name        sname               servicename        
service_reference   sref                serviceref         
shortinfo           shortdesc           description        
start_time [#f1]_   begin_timestamp     begin              
stop_time [#f1]_    -- n/a --           end                
title               title               name               
=================== =================== ===================

.. rubric:: Footnotes
.. [#f1] :py:class:`datetime.datetime` instances.
.. [#f2] :py:class:`datetime.timedelta` instances.