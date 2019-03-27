function statistics_data = extract_topic_statistics(filename, range, type)
    
    data = genericExtractor(filename);
    
    
    if strcmp(type,'thermal')
        statis_topic_1 = {'/vision_tracking/thermal_image','/rgbdt_fusion/velodyne_points_no_human','/rgbdt_fusion/human_center_cloud2','/husky1/octomap_full'};
    else
        statis_topic_1 = {'/vision_tracking/rgb_image','/rgbdt_fusion/velodyne_points_no_human','/rgbdt_fusion/human_center_cloud2','/husky1/octomap_full'};
    end
   
    topic_name_1 = {'image_1', 'velodyne_no_human_1','human_center_1','octomap_full_1'};
%     statis_topic_2 ={'/vision_tracking/rgb_image1','/rgbdt_fusion/velodyne_points_no_human2','/rgbdt_fusion/human_center_cloud2_husky2','/husky2/octomap_full'};
%     topic_name_2 = {'image_2', 'velodyne_no_human_2','human_center_2','octomap_full_2'};
%     
    for i = 1:length(statis_topic_1)
        index = find(contains(data.topic,statis_topic_1{i}));
        start_time = data.window_start_secs(2) + data.window_start_nsecs(2)*1e-9;
        time = [];
        traffic_temp = [];traffic_temp(1)=0;
        for j = 1:length(index)
            if contains(statis_topic_1{i},'/octomap_full')
                time(j) = data.window_stop_secs(index(j)) + data.window_stop_nsecs(index(j))*1e-9 - start_time;
                if j == 1
                    traffic_temp(j) = data.traffic(index(j));
                else
                    traffic_temp(j) = traffic_temp(end) + abs(data.traffic(index(j))-data.traffic(index(j-1)));
                end
            else
                time(j) = data.window_stop_secs(index(j)) + data.window_stop_nsecs(index(j))*1e-9 - start_time;
                traffic_temp(j) = traffic_temp(end) + data.traffic(index(j));
            end
        end
        eval(strcat('statistics_data.',topic_name_1{i},'.traffic = traffic_temp'));
        eval(strcat('statistics_data.',topic_name_1{i},'.time = time'));
    end
    
    if exist('statis_topic_2')
        for i = 1:length(statis_topic_2)
            index = find(contains(data.topic,statis_topic_2{i}));
            start_time = data.window_start_secs(index(1)) + data.window_start_nsecs(index(1))*1e-9;
            time = [];
            traffic_temp = [];traffic_temp(1)=0;
            for j = 1:length(index)
                if contains(statis_topic_2{i},'/octomap_full')
                    time(j) = data.window_stop_secs(index(j)) + data.window_stop_nsecs(index(j))*1e-9 - start_time;
                    if j == 1
                        traffic_temp(j) = data.traffic(index(j));
                    else
                        traffic_temp(j) = traffic_temp(end) + abs(data.traffic(index(j))-data.traffic(index(j-1)));
                    end
                else
                    time(j) = data.window_stop_secs(index(j)) + data.window_stop_nsecs(index(j))*1e-9 - start_time;
                    traffic_temp(j) = traffic_temp(end) + data.traffic(index(j));
                end
            end
            eval(strcat('statistics_data.',topic_name_2{i},'.traffic = traffic_temp'));
            eval(strcat('statistics_data.',topic_name_2{i},'.time = time'));
        end
    end
    figure;
    plot(statistics_data.image_1.time, log10(statistics_data.image_1.traffic), '--','Linewidth',1.5); hold on;
    plot(statistics_data.velodyne_no_human_1.time, log10(statistics_data.velodyne_no_human_1.traffic), ':','Linewidth',1.5); hold on;
    plot(statistics_data.human_center_1.time, log10(statistics_data.human_center_1.traffic), '-.','Linewidth',1.5); hold on;
    temp_traffic = [];traffic = [];
    temp_traffic = log10(statistics_data.octomap_full_1.traffic);
%     7.5 7.477 7.39
%     range = [6.2,7.39]
    traffic =range(1) + (temp_traffic - min(temp_traffic))/(max(temp_traffic)-min(temp_traffic)) * (range(2)-range(1));
    plot(statistics_data.octomap_full_1.time, traffic, '-','Linewidth',1.5);
    lhandle = legend('Raw Image','Raw Point Cloud','Human State','3D map');
    set(gcf,'Position', [713 566 640 420],'Color',[1,1,1]);
    set(gca, 'YLim',[2 10],'FontSize',13);
    set(lhandle, 'Position', [0.6177 0.1511 0.2687 0.1940]);
    
    space = -50;
    
    if strcmp(type,'thermal')
        add = 0;
    else
        add = -30;
    end
    
    text(space + add,3, 'KB','FontSize',13);
    text(space + add,6, 'MB','FontSize',13);
    text(space + add,9, 'GB','FontSize',13);
    xlabel('Tims(s)')
    m = ylabel('Log_{10}(Bytes)');
    set(m,'Position',[-47.7633 + add    5.6810   -1.0000]);
    
%     figure;
%     plot(statistics_data.image_2.time, log10(statistics_data.image_2.traffic)); hold on;
%     plot(statistics_data.velodyne_no_human_2.time, log10(statistics_data.velodyne_no_human_2.traffic)); hold on;
%     plot(statistics_data.human_center_2.time, log10(statistics_data.human_center_2.traffic)); hold on;
%     temp_traffic = [];traffic = [];
%     temp_traffic = log10(statistics_data.octomap_full_2.traffic);
%     traffic = 6 + (temp_traffic - min(temp_traffic))/(max(temp_traffic)-min(temp_traffic)) * (7.8-6);
%     plot(statistics_data.octomap_full_2.time, traffic);
%     legend('Image','Velodyne','Human','Octomap');
    
end