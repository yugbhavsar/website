# from django.db import models
# from wagtail.core.models import Page
# import uuid



# class AbstractVerification( models.Model ):
#     class Meta:
#         abstract = True

#     superseeded_by_login = True

#     is_verified = models.BooleanField(
#         default = False,
#     )

    

# class Auth2PageRelation ( models.Model ):

#     def __init__( self, *args, **kwargs ):
#         super(Auth2PageRelation, self).__init__(*args, **kwargs)
#         self.unique_id = uuid.uuid4()
#         if 'page' in kwargs:
#             self.page = kwargs['page']


#     unique_id = models.CharField(
#         max_length = 64,
#     )
#     page = models.ForeignKey(
#         Page, 
#         on_delete= models.CASCADE
#     )
