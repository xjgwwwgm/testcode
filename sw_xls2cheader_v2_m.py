#! /usr/bin/python3

import os, sys, re, xlrd
from optparse import OptionParser
from pathlib import Path

#parsing cmd option

def pre_work():
    global IP_name, xls_file , out_file
    usage = """usage: sw_xls2cheader [options]
        -n IP_name, must be specified.
        -f/-o must be specified.
        for example:
        sw_xls2cheader_v2.py -n DMAC -f reg.xls -o sa_dmac_reg
        generated sa_dmac_reg.h and sa_dmac_reg.c
        """

    try:
        opt = OptionParser(usage=usage)
        opt.add_option('-n','--ipname',dest="ipname")
        opt.add_option('-f','--xlsfile',dest="xlsfile")
        opt.add_option('-o','--outfile',dest="outfile")
        opts,args = opt.parse_args()
        IP_name = opts.ipname
        xls_file = opts.xlsfile
        out_file = opts.outfile

    except Exception as ex:
        opt.print_help()
        sys.exit(0)

def open_xls():
    global ws,sheet_name

    wb = xlrd.open_workbook(xls_file)
    #print (sheet_name)
    #if sheet_name == None:
    ws = wb.sheet_by_index(0)
    sheet_name_list = wb.sheet_names()
    #sheet_name = sheet_name_list[0]
    #else:
    #    ws = wb.sheet_by_name(sheet_name)

def get_xls_info():
    #get BASE ADDR key word
    str_base_addr_match = re.compile(r"BASE_ADDR")
    #print(str_base_addr_match)
    judge_block_list = ws.col_values(0,start_rowx=0,end_rowx=None)
    #print(judge_block_list)
    block_start_row_list = []
    for col0_rown in range (len(judge_block_list)):
        if str_base_addr_match.search(str(judge_block_list[col0_rown])) :
            block_start_row_list.append(col0_rown)
    block_start_row_list.append(col0_rown)

    #get_block_info
    global blk_reg_offset_list, blk_reg_name_list, blk_reg_note_list
    global blk_field_attr_list, blk_field_width_list, blk_field_name_list, blk_field_note_list
    #get base addr
    global base_addr,blk_consecutive_dict
    base_addr = str(ws.cell_value(0,1)).split(".")[0]
    base_addr = base_addr.replace("0x","").replace("0X","").replace("_","")#统一格式0x 0X 或者没有
    #print(base_addr)
    ##get register offset
    blk_reg_offset_list = []
    blk_reg_name_list = []
    blk_reg_note_list = []
    blk_field_attr_list = []
    blk_field_width_list = []
    blk_field_name_list = []
    blk_field_note_list = []
    blk_consecutive_dict = {}
    #get_blk_info list
    for blk_row_cnt in range(len(block_start_row_list)):
        if blk_row_cnt != 0:
            blk_start_row = block_start_row_list[blk_row_cnt-1]
            blk_end_row = block_start_row_list[blk_row_cnt]+1
            print(blk_start_row)
            print(blk_end_row)
            reg_offset_list = []
            reg_name_list = []
            reg_note_list = []
            reg_start_row_list = []
            for reg_row_cnt in range(blk_start_row+2,blk_end_row):
                #print(reg_row_cnt)
                if ws.cell_type(reg_row_cnt,0) != 0:
                    reg_start_row_list.append(reg_row_cnt)
                    if ws.cell_type(reg_row_cnt,0) == 2:
                        reg_offset_str = str(int(ws.cell_value(reg_row_cnt,0)))
                        reg_offset_list.append(int(reg_offset_str,16))
                    else :
                        reg_offset_str = ws.cell_value(reg_row_cnt,0)
                        #print(reg_offset_str)
                        reg_offset_list.append(int(reg_offset_str,16))
                    reg_name_list.append(ws.cell_value(reg_row_cnt,1))
                    #print(ws.cell_value(reg_row_cnt,1))
                    reg_note_list.append(ws.cell_value(reg_row_cnt,6))
            reg_start_row_list.append(blk_end_row)
            blk_reg_offset_list.append(reg_offset_list)
            blk_reg_name_list.append(reg_name_list)
            blk_reg_note_list.append(reg_note_list)
            #get_reg_info list
            reg_field_attr_list = []
            reg_field_width_list = []
            reg_field_name_list = []
            reg_field_note_list = []
            cur_union_name = ""
            for reg_rown in range(len(reg_start_row_list)):
                if reg_rown != 0:
                    reg_start_row = reg_start_row_list[reg_rown-1]
                    reg_end_row = reg_start_row_list[reg_rown] #+1
                    #print("#################")
                    #print(reg_start_row)
                    #print(reg_end_row)
                    #print("#################")
                    field_attr_list = []
                    field_width_list = []
                    field_name_list = []
                    field_note_list = []
                    reserved_index=0
                    field_attribute_cur = 0
                    for field_row_cnt in range(reg_start_row,reg_end_row):
                        if ws.cell_type(field_row_cnt,2) != 0:
                            field_attribute_cur = ws.cell_value(field_row_cnt,2)
                            field_attr_list.append(field_attribute_cur)
                        else:
                            field_attr_list.append(field_attribute_cur)
                        #print(field_row_cnt)
                        #print(field_attribute_cur)
                        field_width_list.append(ws.cell_value(field_row_cnt,3))
                        field_name = ws.cell_value(field_row_cnt,4).lower().replace("(","").replace(")","")
                        if field_name == ("reserved"):
                            reserved_index = reserved_index + 1
                        if field_name == ("reserved") and reserved_index > 1 :
                            field_name_list.append(field_name+str(reserved_index-1))
                        else :
                            field_name_list.append(field_name)
                        field_note_list.append(ws.cell_value(field_row_cnt,6))
                        if len(ws.cell_value(field_row_cnt,1).strip()) != 0 :
                            cur_union_name = ws.cell_value(field_row_cnt,1)
                            #print("----------"+cur_union_name)
                        #print("#########################::::")
                        #print(ws.ncols)
                        if ws.ncols>=9:
                            if ws.cell_value(field_row_cnt,8) == "consecutive" :
                                #print("####:"+cur_union_name)
                                if len(ws.cell_value(field_row_cnt,1).strip()) != 0 :
                                    blk_consecutive_dict[ws.cell_value(field_row_cnt,1).upper()+"_U"] = int(ws.cell_value(field_row_cnt,9))
                                else:
                                    blk_consecutive_dict[cur_union_name+"_U"] = int(ws.cell_value(field_row_cnt,9))
                            else :
                                blk_consecutive_dict[ws.cell_value(field_row_cnt,1).upper()+"_U"] = 0
                                #print("field_attr_list");
                                #print(field_attr_list);
                                #print("field_width_list");
                                #print(field_width_list);
                                #print("field_name_list");
                                #print(field_name_list);
                                #print("field_note_list");
                                #print(field_note_list);
                        else :
                                blk_consecutive_dict[ws.cell_value(field_row_cnt,1).upper()+"_U"] = 0
                    reg_field_attr_list.append(field_attr_list)
                    reg_field_width_list.append(field_width_list)
                    reg_field_name_list.append(field_name_list)
                    reg_field_note_list.append(field_note_list)
                    #print("reg_field_attr_list");
                    #print(reg_field_attr_list);
                    #print("reg_field_width_list");
                    #print(reg_field_width_list);
                    #print("reg_field_name_list");
                    #print(reg_field_name_list);
                    #print("reg_field_note_list");
                    #print(reg_field_note_list);
            blk_field_attr_list.append(reg_field_attr_list)
            blk_field_width_list.append(reg_field_width_list)
            blk_field_name_list.append(reg_field_name_list)
            blk_field_note_list.append(reg_field_note_list)
        #print("blk_consecutive_dict:")
        #print(blk_consecutive_dict)
        #print("blk_reg_name_list:")
        #print(blk_reg_name_list)

def write_hfile():
    #print(sys.argv[6].upper())
    global file_fp, h_out_file
    h_out_file = out_file+".h"
    file_fp = open(h_out_file,"w")
    #print(base_addr)
    cur_name_index = 0
    cur_addr = IP_name.upper()+"_REG_BASE"
    file_fp.write("#ifndef __SA_{}_H__\n".format(IP_name.upper()))
    file_fp.write("#define __SA_{}_H__\n".format(IP_name.upper()))
    file_fp.write("\n")
    file_fp.write("#ifdef __cplusplus\n")
    file_fp.write("#if __cplusplus\n")
    file_fp.write("extern \"C\" {\n")
    file_fp.write("#endif\n")
    file_fp.write("#endif /* End of #ifdef __cplusplus */\n")
    file_fp.write("\n#define "+cur_addr.ljust(25)+"0x"+base_addr+"\n")
    for blk_name_idx_cnt in range(len(blk_reg_name_list)):
        reg_union_name = []
        cur_offset_list = blk_reg_offset_list[blk_name_idx_cnt].copy()
        cur_name_list = blk_reg_name_list[blk_name_idx_cnt].copy()
        cur_reg_note_list = blk_reg_note_list[blk_name_idx_cnt].copy()
        cur_reg_field_name_array = blk_field_name_list[blk_name_idx_cnt].copy()
        cur_reg_field_attr_array = blk_field_attr_list[blk_name_idx_cnt].copy()
        cur_reg_field_width_array = blk_field_width_list[blk_name_idx_cnt].copy()
        cur_reg_field_note_array = blk_field_note_list[blk_name_idx_cnt].copy()
        for reg_name_idx in range(len(cur_name_list)):
            file_fp.write("#define "+cur_name_list[reg_name_idx].ljust(25).upper()+" "+hex(cur_offset_list[reg_name_idx])+"\n")
        # register describe
        for reg_note_idx in range(len(cur_reg_note_list)):
            cur_field_name_array = cur_reg_field_name_array[reg_note_idx].copy()
            cur_field_attr_array = cur_reg_field_attr_array[reg_note_idx].copy()
            cur_field_width_array = cur_reg_field_width_array[reg_note_idx].copy()
            cur_field_note_array = cur_reg_field_note_array[reg_note_idx].copy()
            reg_note_str = cur_reg_note_list[reg_note_idx]
            reg_note_str_array = reg_note_str.split("\n")
            #print (reg_note_str_array)
            file_fp.write("/** \n")
            file_fp.write("  =========================================================\n")
            store_str_list = []
            for note_str_idx in range(len(reg_note_str_array)):
                deal_note_str = reg_note_str_array[note_str_idx]
                str_align_flag = 0
                str_start_cnt = 0
                for str_idx in range(len(deal_note_str)):
                    if str_idx != 0 and str_idx%80 == 0:
                        str_align_flag = 1
                    if str_align_flag == 1:
                        if deal_note_str[str_idx] == " ":
                             store_str = deal_note_str[str_start_cnt:str_idx] + "\n"
                             store_str_list.append(store_str)
                             str_start_cnt = str_idx+1
                             str_align_flag = 0
                store_str = deal_note_str[str_start_cnt:]+"\n"
                store_str_list.append(store_str)
                #file_fp.write("  "+reg_note_str_array[note_str_idx]+"\n")
            for store_str_idx in range(len(store_str_list)):
                file_fp.write("  "+store_str_list[store_str_idx])
            field_read_flag = 0
            field_write_flag = 0
            for cur_reg_attr in cur_field_attr_array:
                if cur_reg_attr.find("R") != -1:
                    field_read_flag = 1;
                if cur_reg_attr.find("W") != -1:
                    field_write_flag = 1;
            if field_read_flag == 1 and field_write_flag == 1:
                reg_attr_str = "RW"
            if field_read_flag == 1 and field_write_flag != 1:
                reg_attr_str = "RO"
            if field_read_flag != 1 and field_write_flag == 1:
                reg_attr_str = "WO"

            file_fp.write("  -32bit "+reg_attr_str+"\n")
            file_fp.write("  =========================================================\n")
            file_fp.write("*/ \n")
            #register union
            file_fp.write("typedef volatile union {\n")
            file_fp.write("\tstruct {\n")
            cur_field_note_array.reverse()
            cur_field_width_array.reverse()
            cur_field_attr_array.reverse()
            cur_field_name_array.reverse()
            cur_field_width_bit = 0
            for field_idx_cnt in range(len(cur_field_note_array)):
                #field name and width
                field_width_str = cur_field_width_array[field_idx_cnt]
                field_width_match = re.compile(r"\[(\d+):*(\d*)\]")
                field_width_match_obj = field_width_match.match(field_width_str)
                if field_width_match_obj.group(2) == "":
                    low_width_bit = field_width_match_obj.group(1)
                    field_width_bit = 1
                else:
                    low_width_bit = field_width_match_obj.group(2)
                    field_width_bit = int(field_width_match_obj.group(1)) - int(field_width_match_obj.group(2)) + 1
                if int(low_width_bit) > int(cur_field_width_bit):
                    #write reserved
                    file_fp.write("\t\tunsigned int reserved_ro:"+str(int(low_width_bit)-cur_field_width_bit)+";\t/*["+str(int(low_width_bit)-1)+":"+str(cur_field_width_bit)+"]*/\n");
                cur_field_width_bit = int(low_width_bit)+field_width_bit
                #
                field_name_match = re.compile(r"(\w+)")
                field_name_match_obj = field_name_match.search(cur_field_name_array[field_idx_cnt])
                #print(field_name_match_obj)
                field_name_str = field_name_match_obj.group()
                #print(field_name_str)
                field_attr_str = cur_field_attr_array[field_idx_cnt].lower()

                store_str_list = []
                field_note_str = cur_field_note_array[field_idx_cnt]
                field_note_str_list = field_note_str.split("\n")
                for cur_str_idx in range(len(field_note_str_list)):
                    str_align_flag = 0
                    str_start_cnt = 0
                    cur_field_note_str = field_note_str_list[cur_str_idx]
                    for str_idx in range(len(cur_field_note_str)):
                        if str_idx != 0 and str_idx%68 == 0:
                            str_align_flag = 1
                        if str_align_flag == 1:
                            if field_note_str[str_idx] == " ":
                                 store_str = field_note_str[str_start_cnt:str_idx] + "\n"
                                 store_str_list.append(store_str)
                                 str_start_cnt = str_idx+1
                                 str_align_flag = 0
                    store_str = cur_field_note_str[str_start_cnt:]+"\n"
                    store_str_list.append(store_str)
                #field note
                file_fp.write("\t\t/*")
                #file_fp.write(field_note_str)
                for str_wr_idx in range(len(store_str_list)):
                    file_fp.write("\t"+ store_str_list[str_wr_idx])
                    file_fp.write("\t\t")
                #print (store_str_list)
                file_fp.write("*/\n")
                #
                file_fp.write("\t\tunsigned int "+field_name_str+"_"+field_attr_str+":"+str(field_width_bit)+";\t/*"+field_width_str+"*/\n")
                cur_name_index = cur_name_index + 1
            #align 32
            if cur_field_width_bit < 32:
                file_fp.write("\t\tunsigned int reserved_ro:"+str(32-cur_field_width_bit)+";\t/*[31:"+str(cur_field_width_bit)+"]*/\n")
            file_fp.write("\t};\n")
            #write int u32
            file_fp.write("\tunsigned int u32;\n")
            #
            reg_header_name = cur_name_list[reg_note_idx].upper()+"_U"
            reg_union_name.append(reg_header_name)
            file_fp.write("} "+reg_header_name+";\n")
            file_fp.write("\n")
        file_fp.write("typedef struct {\n")
        reg_offset_addr = 0
        rev_index = 0
        #print(reg_union_name)
        for reg_union_cnt in range(len(reg_union_name)):
            #print (cur_offset_list[reg_union_cnt])
            if cur_offset_list[reg_union_cnt] > reg_offset_addr :
                reg_offset_size = (cur_offset_list[reg_union_cnt] - reg_offset_addr)/4
                file_fp.write("\tunsigned int rev"+str(rev_index)+"["+str(int(reg_offset_size))+"];\n")
                #print (reg_offset_size)
                rev_index = rev_index + 1
            #print(blk_consecutive_dict)
            if int(blk_consecutive_dict[reg_union_name[reg_union_cnt]]) == 0:
                file_fp.write("\t"+reg_union_name[reg_union_cnt]+" "+cur_name_list[reg_union_cnt].lower()+";\n")
                reg_offset_addr = cur_offset_list[reg_union_cnt] + 4
            else :
                file_fp.write("\t"+reg_union_name[reg_union_cnt]+" "+cur_name_list[reg_union_cnt].lower()+"["+str(blk_consecutive_dict[reg_union_name[reg_union_cnt]])+"];\n")
                reg_offset_addr = cur_offset_list[reg_union_cnt] + 4*int(blk_consecutive_dict[reg_union_name[reg_union_cnt]])

        file_fp.write("} "+IP_name+"_"+str(blk_name_idx_cnt)+"_REG_S;\n")
        file_fp.write("\n")



    file_fp.write("#ifdef __cplusplus\n")
    file_fp.write("#if __cplusplus\n")
    file_fp.write("}\n")
    file_fp.write("#endif\n")
    file_fp.write("#endif /* End of #ifdef __cplusplus */\n")

    file_fp.write("#endif /* __SA_{}_H__ */\n".format(IP_name.upper()))
    file_fp.write("\n")
    file_fp.close()

def write_cfile():
    global IP_name,h_out_file
    c_out_file = out_file+".c"
    file_fp = open(c_out_file,"w")
    field_reserved_match = re.compile(r"reserved")
    field_width_match = re.compile(r"\[(\d+):*(\d*)\]")
    #write head
    file_fp.write("\n#include \"sa_type.h\"\n")
    file_fp.write("#include \""+h_out_file+"\"\n")
    file_fp.write("#include \"sa_base_define.h\"\n")
    for blk_reg_name_idx in range(len(blk_reg_name_list)):
        cur_reg_name_list = blk_reg_name_list[blk_reg_name_idx].copy()
        cur_blk_field_name_list = blk_field_name_list[blk_reg_name_idx].copy()
        cur_blk_field_note_list = blk_field_note_list[blk_reg_name_idx].copy()
        cur_blk_field_attr_list = blk_field_attr_list[blk_reg_name_idx].copy()
        cur_blk_field_width_list = blk_field_width_list[blk_reg_name_idx].copy()
        for reg_name_idx in range(len(cur_reg_name_list)):
            cur_reg_field_name_list = cur_blk_field_name_list[reg_name_idx].copy()
            cur_reg_field_note_list = cur_blk_field_note_list[reg_name_idx].copy()
            cur_reg_field_attr_list = cur_blk_field_attr_list[reg_name_idx].copy()
            cur_reg_field_width_list = cur_blk_field_width_list[reg_name_idx].copy()
            reg_name_str = cur_reg_name_list[reg_name_idx]
            #print ("reg_name_str:")
            #print (reg_name_str)
            #函数注释
            funanno = ""
            #函数名
            funname = ""
            #函数开始定义
            funbeg = ""
            #函数内容
            funcontent=""
            #函数结束定义
            funend = ""

            #函数注释
            funranno = ""
            #函数名
            funrname = ""
            #函数开始定义
            funrbeg = ""
            #函数内容
            funrcontent=""
            #函数结束定义
            funrend = ""
            field_name_len = len(cur_reg_field_name_list)
            for field_name_idx in range(field_name_len):
                if field_name_idx == 0:
                    field_first_valid_index = 0
                    funanno = ""
                    funname = ""
                    funbeg = ""
                    funcontent=""
                    funend = ""
                    funranno = ""
                    funrname = ""
                    funrbeg = ""
                    funrcontent=""
                    funrend = ""
                    funname = "static inline SA_VOID "+reg_name_str.lower()+"_set (SA_VOID *pbase_addr "
                    funbeg = "{\n"+"\tSA_U32 reg_value;\n"
                    funrname = "static inline SA_VOID "+reg_name_str.lower()+"_get (SA_VOID *pbase_addr "
                    funrbeg = "{\n"+"\tSA_U32 reg_value;\n"
                field_name_str = cur_reg_field_name_list[field_name_idx]
                field_note_str = cur_reg_field_note_list[field_name_idx]
                field_attr_str = cur_reg_field_attr_list[field_name_idx]
                field_width_str = cur_reg_field_width_list[field_name_idx]
                field_reserved_match_obj = field_reserved_match.search(field_name_str)
                field_width = 0
                
                field_note_str.replace("\n","\n*")
                if field_reserved_match_obj :
                    pass
                else :
                    field_width_match_obj = field_width_match.match(field_width_str)
                    if field_width_match_obj.group(2) == "":
                        field_width = 1
                        field_width_start = field_width_match_obj.group(1)
                    else:
                        field_width_start= field_width_match_obj.group(1)
                        field_width_end = field_width_match_obj.group(2)
                        if field_width_start == field_width_end :
                            field_width = 1
                        print("int(field_width_end)=%d - int(field_width_start)=%d=%d\n"%(int(field_width_end), int(field_width_start), abs(int(field_width_end) - int(field_width_start))+1))
                    if field_attr_str.find("W") != -1:
                        if field_width == 1:
                            funname+=",SA_U8 "+field_name_str.lower()
                            funbeg = "{\n" +"\tSA_U32 reg_value;\n"
                            funcontent+="\treg_value = SA_REG_READL((SA_U8 *)pbase_addr + " + reg_name_str.upper() +");\n "
                            funcontent+="\tif("+field_name_str.lower()+")\n"
                            funcontent+="\t\tSA_SET_BIT(reg_value, SA_FIELD_BIT_"+field_width_start+");\n"
                            funcontent+="\telse\n"
                            funcontent+="\t\tSA_CLEAR_BIT(reg_value, SA_FIELD_BIT_"+field_width_start+");\n"
                            funcontent+="\tSA_REG_WRITEL(reg_value,(SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                        else:
                            diccount=int(blk_consecutive_dict[reg_name_str.upper()+"_U"])
                            if  diccount == 0:
                                str_pattern_gain = re.compile(r".*[e|d|3]_gain")
                                if re.findall(str_pattern_gain,funname):
                                    funname+=", SA_U16 "+field_name_str.lower()
                                    print("field_name_idx is %d field_first_valid_index=%d %s"%(field_name_idx,field_first_valid_index, funname));
                                elif (abs(int(field_width_end) - int(field_width_start))+1 > 19):
                                    funname+=", SA_U32 "+field_name_str.lower()
                                else:
                                    funname+=", SA_U8 "+field_name_str.lower()
                                    #print("field_name_idx is %d %s"%(field_name_idx,funname));
                                #if field_name_idx == 0:
                                if field_first_valid_index == 0:
                                    funcontent+="\treg_value = SA_REG_READL((SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                                    #print("#####field_name_idx is %d %s"%(field_name_idx,funname));
                                
                                funcontent+="\treg_value = SA_SET_BITS_VALUE(reg_value, "+field_name_str.lower()+",SA_FIELD_BIT_"+field_width_end+", SA_FIELD_BIT_"+field_width_start+");\n"
                                
                                if field_name_idx == (field_name_len-1):
                                    funcontent+="\tSA_REG_WRITEL(reg_value, (SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                            else :
                                if funname.find("kb") != -1:
                                    funname+=",SA_S16 *"+field_name_str.lower()
                                elif funname.find("lut") != -1:
                                    funname+=",SA_S32 *"+field_name_str.lower()
                                elif (abs(int(field_width_end) - int(field_width_start))+1 > 19):
                                    funname+=",SA_U32 *"+field_name_str.lower()
                                else:
                                    funname+=",SA_U8 *"+field_name_str.lower()
                                funcontent+="\t\treg_value = SA_SET_BITS_VALUE(reg_value, "+field_name_str.lower()+"[idx],SA_FIELD_BIT_"+field_width_end+", SA_FIELD_BIT_"+field_width_start+");\n"
                    if field_attr_str.find("R") != -1:
                        if field_width == 1:
                            funrname+=", SA_U8 *"+field_name_str.lower()
                            funrcontent +="\treg_value = SA_REG_READL((SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                            funrcontent +="\t*"+field_name_str.lower()+"= SA_GET_BIT(reg_value,SA_FIELD_BIT_"+field_width_start+");\n"
                            #file_fp.write("}\n")
                        else:
                            if int(blk_consecutive_dict[reg_name_str.upper()+"_U"]) == 0:
                                str_pattern_gain = re.compile(r".*[e|d|3]_gain")
                                if re.findall(str_pattern_gain,funrname):
                                    funrname+=", SA_U16 *"+field_name_str.lower()
                                elif (abs(int(field_width_end) - int(field_width_start))+1 > 19):
                                    funrname+=",SA_U32 *"+field_name_str.lower()
                                else:
                                    funrname+=", SA_U8 *"+field_name_str.lower()
                                funrcontent += "\treg_value = SA_REG_READL((SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                                funrcontent += "\t*"+field_name_str.lower()+"= SA_GET_BITS(reg_value, SA_FIELD_BIT_"+field_width_end+",SA_FIELD_BIT_"+field_width_start+");\n"
                            else :
                                '''funrname+=", SA_U32 *"+field_name_str.lower()'''
                                if funrname.find("kb") != -1:
                                    funrname+=",SA_S16 *"+field_name_str.lower()
                                elif funrname.find("lut") != -1:
                                    funrname+=",SA_S32 *"+field_name_str.lower()
                                elif (abs(int(field_width_end) - int(field_width_start))+1 > 19):
                                    funrname+=",SA_U32 *"+field_name_str.lower()
                                else:
                                    funrname+=",SA_U8 *"+field_name_str.lower()
                                funrcontent +="\t\t"+field_name_str.lower()+"[idx] = SA_GET_BITS(reg_value, SA_FIELD_BIT_{},SA_FIELD_BIT_{});\n".format(field_width_end,field_width_start)

                    field_first_valid_index+=1
                if field_name_idx == (field_name_len-1):
                    if funcontent!= "":
                        funname+=")\n"
                        file_fp.write(funanno)
                        file_fp.write(funname)
                        diccount = int(blk_consecutive_dict[reg_name_str.upper()+"_U"])
                        if diccount>0 :
                            funbeg += "\tint  idx;\n"
                            funbeg +="\tfor (idx = 0; idx < "+str(diccount)+"; idx++)\n"
                            funbeg +="\t{\n"
                            funbeg+="\t\treg_value = SA_REG_READL((SA_U8 *)pbase_addr + "+reg_name_str.upper()+" +sizeof(SA_U32)*idx);\n"
                        '''else :
                            funcontent+="\tSA_REG_WRITEL(reg_value, (SA_U8 *)pbase_addr + "+reg_name_str.upper()+");\n"
                        '''
                        file_fp.write(funbeg)
                        file_fp.write(funcontent)
                        if diccount >0 :
                            funend+="\t\tSA_REG_WRITEL(reg_value, (SA_U8 *)pbase_addr + "+reg_name_str.upper()+"+sizeof(SA_U32)*idx);\n"
                            funend +="\t}\n"
                            
                        funend+="}\n"
                        file_fp.write(funend)

                    if funrcontent != "":
                        funrname+=")\n"
                        file_fp.write(funranno)
                        file_fp.write(funrname)
                        if diccount >0 :
                            funrbeg += "\tint  idx;\n"
                            funrbeg +="\tfor (idx = 0; idx < "+str(diccount)+"; idx++)\n"
                            funrbeg +="\t{\n"
                            funrbeg +="\t\treg_value = SA_REG_READLS((SA_U8 *)pbase_addr + "+reg_name_str.upper()+" +sizeof(SA_U32)*idx);\n"
                        file_fp.write(funrbeg)
                        file_fp.write(funrcontent)
                        if diccount > 0 :
                            funrend +="\t}\n"
                        funrend+="}\n"
                        file_fp.write(funrend)
    file_fp.close()

if __name__ == "__main__":
    pre_work()
    open_xls()
    get_xls_info()
    write_hfile()
    write_cfile()
