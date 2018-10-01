from website.pdfhandling import RUBPDF, RUBIONPDF

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

       
        
class RUBIONBadge ( RUBIONPDF ):
    height = 40 * mm
    width = 75 * mm
    
    def __init__( 
            self, 
            first_name,
            last_name,
            workgroup,
            title = None,
            coat_size = None,
            shoe_size = None,
            entrance = None
    ):
        super(RUBIONBadge, self).__init__()

        self.center_canvas()
        self.draw_canvas_rect()

        self.rubionlogo(15*mm, 0.05*self.width, 0.9*self.height-15*mm/8)

        self.font_flama(12, self.WEIGHT_BOLD)
        self.pdf.setFillColor(self.BLACK)
        if title:
            self.pdf.drawCentredString(self.width/2, 3*self.height/5, "{} {} {}".format(title, first_name, last_name))
        else:
            self.pdf.drawCentredString(self.width/2, 3*self.height/5, "{} {}".format(first_name, last_name))

        self.font_flama(10)
        self.pdf.setFillColor(self.RUBBLUE)
        self.pdf.drawCentredString(self.width/2, 3*self.height/5-5*mm, workgroup.title_de)
            
        self.pdf.setFillColor(self.BLACK)
        self.font_flama(9)
        if shoe_size:
            self.pdf.drawCentredString(self.width/2, 2*mm, "Schuhe: {}".format(shoe_size))
        if coat_size:
            self.pdf.drawString(2*mm, 2*mm, "Kittel: {}".format(coat_size))
        if entrance:
            self.pdf.drawRightString(self.width-2*mm, 2*mm, "Schleuse: {}".format(entrance))


    def center_canvas(self):
        a4width, a4height = A4
        self.pdf.translate((a4width-self.width)/2, (a4height-self.height)/2)

    def draw_canvas_rect(self):
        self.pdf.rect(0,0,self.width, self.height)
