import datetime

from io import BytesIO

import os 

from PyPDF2 import PdfFileWriter, PdfFileReader

from reportlab.pdfgen import canvas
from reportlab.lib.colors import CMYKColor, PCMYKColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PDFFONTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'pdfhandling','fonts')

class RUBPDF(object):

    RUBBLUE  = CMYKColor(1,.5,0,.6)
    RUBGREEN = CMYKColor(.23,0,.85,.24)
    RUBGRAY  = CMYKColor(.03,.03,.03,.1)
    BLACK = CMYKColor(0,0,0,1)
    WHITE = CMYKColor(0,0,0,0)

    WEIGHT_REGULAR = 'R'
    WEIGHT_BOLD = 'Bd'

    def __init__(self, pagesize = A4, templatefile = None):
        pdfmetrics.registerFont(TTFont('FlamaBd', os.path.join(PDFFONTDIR,'RubFlama-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('FlamaR',  os.path.join(PDFFONTDIR,'RubFlama-Regular.ttf')))
        pdfmetrics.registerFont(TTFont('ScalaR',  os.path.join(PDFFONTDIR,'RubScalaTZ.ttf')))
        pdfmetrics.registerFont(TTFont('ScalaBd', os.path.join(PDFFONTDIR,'RubScalaTZBold.ttf')))

        if templatefile:
            self.template_pdf = PdfFileReader(templatefile)
        else:
            self.template_pdf = None
                                
        self.buffer = BytesIO()
        self.pdf = canvas.Canvas(self.buffer, pagesize = pagesize)

    def font_flama(self, size, weight = None, color = BLACK):
        self.pdf.setFillColor(color)
        if not weight:
            weight = self.WEIGHT_REGULAR
        self.pdf.setFont('Flama{}'.format(weight) , size)

    def font_scala(self, size, weight = None, color = BLACK):
        self.pdf.setFillColor(color)
        if not weight:
            weight = self.WEIGHT_REGULAR
        self.pdf.setFont('Scala{}'.format(weight) , size)


    def get_in_response(self, response):
        if not self.template_pdf:
            self.pdf.showPage()
            self.pdf.save()

            response.write(self.buffer.getvalue())
            self.buffer.close()
            return response

    def write2file( self, filename ):
        if self.template_pdf:
            self.pdf.save()
            self.buffer.seek(0)
            new_pdf = PdfFileReader(self.buffer)
            page = self.template_pdf.getPage(0)
            page.mergePage(new_pdf.getPage(0))
            output = PdfFileWriter()
            output.addPage(page)

            output_stream = open( filename, 'wb')
            output.write(output_stream)
            output_stream.close()



class RUBIONPDF ( RUBPDF ):
    def rubionlogo(self, width, posx, posy):
        block_width = width/4
        gap = block_width/2

        for color in [self.RUBBLUE, self.RUBGREEN, self.RUBGRAY]:
            self.pdf.setStrokeColor(color)
            self.pdf.setFillColor(color)
            self.pdf.rect(posx, posy, block_width, block_width, fill=1)
            posx += block_width + gap


class RUBLetter( RUBPDF ):
    template_file = 'templates/website/pdf/rub_letter.pdf'

    ALIGN_LEFT = 'l'
    ALIGN_RIGHT = 'r'
    ALIGN_CENTER = 'c'

    def __init__(self, template_file = None, pagesize = None):
        if not template_file:
            template_file = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                self.template_file
            )

        super().__init__( templatefile = template_file, pagesize = pagesize )
        
        left_x = 71
        left2c = 397.48

        self.POSITIONS = {
            'date' : (439, 538,1),
            'subject' : (left_x, 485),
            'address' : (left_x, 675),
            'backaddress' : (left_x, 700),
            'backaddress_regular' : (137.320, 700),
            'institute_l1': (left2c, 710.704),
            'institute_l2': (left2c, 699.624),
            'institute_l3': (left2c, 691.504),
            'person_l1' : (left2c, 670.004),
            'person_l2' : (left2c, 660.404),
            'building' : (left2c, 640.140),
            'street_zip' : (left2c, 628.372),
            'homepage': (left2c, 599.204),
            'phone': (left2c, 579.836),
            'fax' :  (left2c, 567.836),
            'email' : (left2c, 556.052),
            'bottom_address' : (left_x, 19.476+8.65),
            'bottom_access' : (left_x, 4.976+8.65),
            'bottom_address_regular' : (154.780, 19.476+8.65),
            'bottom_access_regular' : (149.984, 4.976+8.65),
            'RUB_homepage' : (490.42, 6.09+8.65),
        }
        self.font_flama(8, self.WEIGHT_BOLD, self.BLACK)
        self._draw_at_pos('bottom_address', 'ADRESSE / ADDRESS')
        self._draw_at_pos('bottom_access', 'ANFAHRT / ACCESS')

        self.font_flama(8, self.WEIGHT_REGULAR, self.BLACK)
        self._draw_at_pos('bottom_address_regular', 'Universitätsstraße 150 | D-44801 Bochum, Germany')
        self._draw_at_pos('bottom_access_regular', 'U-Bahn: U35 | Auto: A43, Abfahrt (19) Bochum Witten')

        self.font_flama(10, self.WEIGHT_BOLD, self.RUBGREEN)
        self._draw_at_pos('RUB_homepage', 'WWW.RUB.DE')


    def _draw_at_pos(self, pos, string, yoffset = 0, align = None ):
        if not align:
            align = self.ALIGN_LEFT

        if align == self.ALIGN_LEFT:
            func = getattr(self.pdf, 'drawString')
        if align == self.ALIGN_RIGHT:
            func = getattr(self.pdf, 'drawRightString')
        if align == self.ALIGN_CENTER:
            func = getattr(self.pdf, 'drawCentredString')
        
        func(self.POSITIONS[pos][0], self.POSITIONS[pos][1]-yoffset, string )



    def _draw_multiline(self, identifier, lines, yoffset = 0):
        c = 1
        for line in lines:
            self._draw_at_pos("{}_l{}".format(identifier, c), line, yoffset)
            c = c + 1

    def draw_street_zip(self, line):
        self.font_flama(8, self.WEIGHT_REGULAR, self.BLACK)
        self._draw_at_pos('street_zip', line)

    def draw_backaddress( self, institute = None ):
        self.font_flama(7, self.WEIGHT_BOLD)
        self._draw_at_pos('backaddress','RUHR-UNIVERSITÄT')
        self.font_flama(7)
        if institute:
            self._draw_at_pos('backaddress_regular','BOCHUM | {} | 44780 Bochum | Germany'. format(institute))
        else:
            self._draw_at_pos('backaddress_regular','BOCHUM | 44780 Bochum | Germany')
        
    def draw_homepage(self, homepage):
        self.font_flama(8,self.WEIGHT_BOLD, self.BLACK)
        self._draw_at_pos('homepage',homepage)

    def _draw_with_prefix( self, identifier, prefix, content, yoffset = 0):
        self._draw_at_pos(identifier,'{}: {}'.format(prefix, content), yoffset)

    def draw_phone(self, phone):
        if phone.startswith('32'):
            phone = phone[2:]
        self.font_flama(8, self.WEIGHT_REGULAR, self.BLACK)
        self._draw_with_prefix('phone', 'Fon', phone)

    def draw_fax(self, fax):
        self.font_flama(8, self.WEIGHT_REGULAR, self.BLACK)
        self._draw_with_prefix('fax', 'Fax', fax)


    def draw_email(self, email):
        self.font_flama(8, self.WEIGHT_REGULAR, self.BLACK)
        self._draw_with_prefix('email', 'E-Mail', email)

    def draw_institute(self, lines):
        self.font_flama(8, self.WEIGHT_BOLD, self.RUBGREEN)
        
        if isinstance(lines, str):
            self._draw_at_pos('institute_l2', lines)
        elif len(lines) == 1:
            self._draw_at_pos('institute_l2', lines[0])
        else:
            if len(lines) == 2:
                yoffset = (self.POSITIONS['institute_l3'][1] - self.POSITIONS['institute_l1'][1])/3
            else:
                yoffset = 0
            self._draw_multiline('institute', lines, yoffset = yoffset)
            
    def draw_building(self, building):
        self.font_flama(8,self.WEIGHT_REGULAR, self.BLACK)
        self._draw_at_pos('building', building)

    def draw_person(self, lines):
        self.font_flama(8,self.WEIGHT_BOLD, self.BLACK)
        self._draw_multiline('person', lines)

    def draw_date( self, date = None ):
        if not date:
            date = datetime.date.today()
        self.font_flama(8)
        self._draw_at_pos('date', str(date))

    def draw_subject( self, subject ):
        self.font_flama(14, self.WEIGHT_BOLD, self.RUBBLUE)
        self._draw_at_pos('subject', subject)

    def draw_address( self, lines ):
        offset = 12
        count = 0
        for line in lines:
            if count in [0, len(lines)-1]:
                self.font_scala(10, self.WEIGHT_BOLD)
            else:
                self.font_scala(10)
            self._draw_at_pos('address', line, yoffset = count * offset)
            count = count + 1


class RUBIONLetter ( RUBLetter, RUBIONPDF ) :
    
    def __init__(self, staff, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draw_backaddress('RUBION')
        self.draw_institute(['RUBION', 'Zentrale Einrichtung für Ionenstrahlen','und Radionuklide'])
        self.draw_homepage('www.rubion.rub.de')

        self.draw_street_zip('Universitätsstraße 150, 44801 Bochum')
        self.draw_phone('+49 234 32-{}'.format(staff.phone))
        self.draw_building('Gebäude {}'.format(staff.room))
        self.draw_email(staff.email)
        if staff.fax:
            self.draw_fax('+49 234 32-{}'.format(staff.fax))

        if staff.grade:
            self.draw_person(["{} {} {}".format(staff.grade, staff.first_name, staff.last_name)])
        else:
            self.draw_person(["{} {}".format(staff.first_name, staff.last_name)])

    
